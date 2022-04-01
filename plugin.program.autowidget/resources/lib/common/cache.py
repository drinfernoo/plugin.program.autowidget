import xbmcgui
import xbmcvfs

import glob
import hashlib
import json
import math
import os
import time

import six

from resources.lib import manage
from resources.lib.common import settings
from resources.lib.common import utils

_addon_data = settings.get_addon_info("profile")

_playback_history_path = os.path.join(_addon_data, "cache.history")

_startup_time = time.time()  # TODO: could get reloaded so not accurate?
DEFAULT_CACHE_TIME = 60 * 5


def clear_cache(target=None):
    if not target:
        dialog = xbmcgui.Dialog()
        choice = dialog.yesno("AutoWidget", utils.get_string(30117))
        del dialog

        if choice:
            for file in [
                i
                for j in xbmcvfs.listdir(_addon_data)
                for i in j
                if i.endswith((".cache", ".history", ".queue", ".time"))
            ]:
                utils.remove_file(os.path.join(_addon_data, file))
    else:
        utils.remove_file(os.path.join(_addon_data, "{}.cache".format(target)))
        utils.update_container(True)


def hash_from_cache_path(path):
    base = os.path.basename(path)
    return os.path.splitext(base)[0]


def iter_queue():
    queued = [
        os.path.join(_addon_data, x)
        for x in xbmcvfs.listdir(_addon_data)[1]
        if x.endswith(".queue")
    ]
    # TODO: sort by path instead so load plugins at the same time

    for path in sorted(queued, key=lambda x: xbmcvfs.Stat(x).st_mtime()):
        queue_data = utils.read_json(path)
        yield queue_data.get("path", "")


def read_history(path, create_if_missing=True):
    hash = path2hash(path)
    history_path = os.path.join(_addon_data, "{}.history".format(hash))
    if not xbmcvfs.exists(history_path):
        if create_if_missing:
            cache_data = {}
            history = cache_data.setdefault("history", [])
            widgets = cache_data.setdefault("widgets", [])
            utils.write_json(history_path, cache_data)
        else:
            cache_data = None
    else:
        cache_data = utils.read_json(history_path)
    return cache_data


def next_cache_queue():
    # Simple queue by creating a .queue file
    # TODO: use watchdog to use less resources
    for path in iter_queue():
        # TODO: sort by path instead so load plugins at the same time
        hash = path2hash(path)
        queue_path = os.path.join(_addon_data, "{}.queue".format(hash))
        if not xbmcvfs.exists(queue_path):
            # a widget update has already taken care of updating this path
            continue
        # We will let the update operation remove the item from the queue

        # TODO: need to workout if a blocking write is happen while it was queued or right now.
        # probably need a .lock file to ensure foreground calls can get priority.
        cache_data = read_history(path, create_if_missing=True)
        widget_id = utils.read_json(queue_path).get("widget_id", None)
        yield path, cache_data, widget_id


def push_cache_queue(path, widget_id=None):
    hash = path2hash(path)
    queue_path = os.path.join(_addon_data, "{}.queue".format(hash))
    history = read_history(path, create_if_missing=True)  # Ensure its created
    changed = False
    if widget_id is not None and widget_id not in history["widgets"]:
        history["widgets"].append(widget_id)
        changed = True
    if history.get("path", "") != path:
        history["path"] = path
        changed = True
    if changed:
        history_path = os.path.join(_addon_data, "{}.history".format(hash))
        utils.write_json(history_path, history)

    if xbmcvfs.exists(queue_path):
        pass  # Leave original modification date so item is higher priority
    else:
        utils.write_json(
            queue_path, {"hash": hash, "path": path, "widget_id": widget_id}
        )


def is_cache_queue(hash):
    queue_path = os.path.join(_addon_data, "{}.queue".format(hash))
    return xbmcvfs.exists(queue_path)


def remove_cache_queue(hash):
    queue_path = os.path.join(_addon_data, "{}.queue".format(hash))
    utils.remove_file(queue_path)


def path2hash(path):
    if path is not None:
        return hashlib.sha1(six.ensure_binary(path, "utf8")).hexdigest()
    else:
        return None


def widgets_for_path(path):
    hash = path2hash(path)
    history_path = os.path.join(_addon_data, "{}.history".format(hash))
    cache_data = utils.read_json(history_path) if os.path.exists(history_path) else None
    if cache_data is None:
        cache_data = {}
    widgets = cache_data.setdefault("widgets", [])
    return set(widgets)


def cache_and_update(path, widget_id, cache_data, notify=None):
    """a widget might have many paths. Ensure each path is either queued for an update
    or is expired and if so force it to be refreshed. When going through the queue this
    could mean we refresh paths that other widgets also use. These will then be skipped.
    """
    assert widget_id
    assert cache_data.get("path") == path
    assert widget_id in cache_data["widgets"]

    hash = path2hash(path)
    if not is_cache_queue(hash):
        return []

    if notify is not None:
        widget_def = manage.get_widget_by_id(widget_id)
        if widget_def is not None:
            notify(widget_def.get("label", ""), path)

    new_files, files_changed = cache_files(path, widget_id)
    remove_cache_queue(hash)

    # TODO: this is all widgets that ever requested this path. do we
    # need to update all of them?
    return cache_data["widgets"] if files_changed else []


def cache_files(path, widget_id):
    info_keys = utils.get_info_keys()
    params = {
        "jsonrpc": "2.0",
        "method": "Files.GetDirectory",
        "params": {
            "properties": info_keys,
            "directory": path,
        },
        "id": 1,
    }
    files = utils.call_jsonrpc(params)
    _, _, changed = cache_expiry(path, widget_id, add=files)
    return (files, changed)


def cache_expiry(path, widget_id, add=None, background=True):
    # Predict how long to cache for with a min of 5min so updates don't go in a loop
    # TODO: find better way to prevents loops so that users trying to manually refresh can do so
    # TODO: manage the cache files to remove any too old or no longer used
    # TODO: update paths on autowidget refresh based on predicted update frequency. e.g. plugins with random paths should
    # update when autowidget updates.
    hash = path2hash(path)
    cache_path = os.path.join(_addon_data, "{}.cache".format(hash))

    # Read file every time as we might be called from multiple processes
    history_path = os.path.join(_addon_data, "{}.history".format(hash))
    cache_data = utils.read_json(history_path) if xbmcvfs.exists(history_path) else None
    if cache_data is None:
        cache_data = {}
        since_read = 0
    else:
        since_read = time.time() - last_read(hash)

    history = cache_data.setdefault("history", [])
    widgets = cache_data.setdefault("widgets", [])
    if widget_id not in widgets:
        widgets.append(widget_id)

    expiry = time.time() - 20
    contents = None
    changed = True
    size = 0

    if add is not None:
        cache_json = json.dumps(add)
        if not add or not cache_json.strip():
            result = "Invalid Write"

        elif "error" in add or not add.get("result", {}).get("files"):
            # In this case we don't want to cache a bad result
            result = "Error"
            # TODO: do we schedule a new update? or put dummy content up even if we have
            # good cached content?
        else:
            utils.write_json(cache_path, add)
            contents = add
            size = len(cache_json)
            content_hash = path2hash(cache_json)
            changed = history[-1][1] != content_hash if history else True
            history.append((time.time(), content_hash))
            if cache_data.get("path") != path:
                cache_data["path"] = path
            utils.write_json(history_path, cache_data)
            # expiry = history[-1][0] + DEFAULT_CACHE_TIME
            pred_dur = predict_update_frequency(history)
            expiry = (
                history[-1][0] + pred_dur * 0.75
            )  # less than prediction to ensure pred keeps up to date
            result = "Wrote"
    else:
        # write any updated widget_ids so we know what to update when we dequeue
        # Also important as wwe use last modified of .history as accessed time
        utils.write_json(history_path, cache_data)
        if not xbmcvfs.exists(cache_path):
            result = "Empty"
            if background:
                contents = utils.make_holding_path(utils.get_string(30143), "refresh")
                push_cache_queue(path)
        else:
            contents = utils.read_json(cache_path, log_file=True)
            if contents is None:
                result = "Invalid Read"
                if background:
                    contents = utils.make_holding_path(
                        utils.get_string(30137).format(hash), "alert"
                    )
                    push_cache_queue(path)
            else:
                # write any updated widget_ids so we know what to update when we dequeue
                # Also important as wwe use last modified of .history as accessed time
                utils.write_json(history_path, cache_data)
                size = len(json.dumps(contents))
                if history:
                    expiry = history[-1][0] + predict_update_frequency(history)

                #                queue_len = len(list(iter_queue()))
                if expiry > time.time():
                    result = "Read"
                elif not background:
                    result = "Skip already updated"
                # elif queue_len > 3:
                #     # Try to give system more breathing space by returning empty cache but ensuring refresh
                #     # better way is to just do this the first X accessed after startup.
                #     # or how many accessed in the last 30s?
                #     push_cache_queue(hash)
                #     result = "Skip (queue={})".format(queue_len)
                #     contents = dict(result=dict(files=[]))
                else:
                    push_cache_queue(path)
                    result = "Read and queue"
    # TODO: some metric that tells us how long to the first and last widgets becomes visible and then get updated
    # not how to measure the time delay when when the cache is read until it appears on screen?
    # Is the first cache read always the top visibible widget?
    utils.log(
        "{} cache {}B (exp:{}, last:{}): {} {}".format(
            result,
            size,
            utils.ft(expiry - time.time()),
            utils.ft(since_read),
            hash[:5],
            widgets,
        ),
        "notice",
    )
    return expiry, contents, changed


def last_read(hash):
    # Technically this is last read or updated but we can change it to be last read Later
    # if we create another file
    path = os.path.join(_addon_data, "{}.history".format(hash))
    return xbmcvfs.Stat(path).st_mtime()


def predict_update_frequency(history):
    if not history:
        return DEFAULT_CACHE_TIME
    update_count = 0
    duration = 0
    changes = []
    last_when, last = history[0]
    for when, content in history[1:]:
        update_count += 1
        if content == last:
            duration += when - last_when
        else:
            duration = (
                +(when - last_when) / 2
            )  # change could have happened any time inbetween
            changes.append((duration, update_count))
            duration = 0
            update_count = 0
        last_when = when
        last = content
    if not changes and duration:
        # drop the last part of the history that hasn't changed yet unless we have no other history to work with
        # This is an underestimate as we aren't sure when in the future it will change
        changes.append((duration, update_count))
    # TODO: the first change is potentially an underestimate too because we don't know how long it was unchanged for
    # before we started recording.

    # Now we have changes, we can do some trends on them.
    durations = [duration for duration, update_count in changes if update_count > 1]
    if not durations:
        return DEFAULT_CACHE_TIME
    med_dur = sorted(durations)[int(math.floor(len(durations) / 2)) - 1]
    avg_dur = sum(durations) / len(durations)
    # weighted by how many snapshots we took inbetween.
    # TODO: number of snapshots inbetween is really just increasing the confidence on the end time bot the duration as a whole.
    # so perhaps a better metric is the error margin of the duration? and not weighting by that completely.
    # ie durations with wide margin of error should be less important. e.g. times kodi was never turned on for months/weeks.
    weighted = sum([d * c for d, c in changes]) / sum([c for _, c in changes])
    # TODO: also try exponential decay. Older durations are less important than newer ones.
    ones = len([c for d, c in changes if c == 1]) / float(len(changes))
    # TODO: if many streaks with lots of counts then its stable and can predict
    utils.log(
        "avg_dur {:0.0f}s, med_dur {:0.0f}s, weighted {:0.0f}s, ones {:0.2f}, all {}".format(
            avg_dur, med_dur, weighted, ones, changes
        ),
        "debug",
    )
    if ones > 0.9:
        # too unstable so no point guessing
        return DEFAULT_CACHE_TIME
    elif DEFAULT_CACHE_TIME > avg_dur / 2.0:
        # should not got less than 5min otherwise our updates go in a loop
        return DEFAULT_CACHE_TIME
    else:
        return (
            avg_dur / 2.0
        )  # we want to ensure we check more often than the actual predicted expiry


#    return DEFAULT_CACHE_TIME


def widgets_changed_by_watching(media_type):
    # Predict which widgets the skin might have that could have changed based on recently finish
    # watching something

    all_cache = [
        os.path.join(_addon_data, x)
        for x in xbmcvfs.listdir(_addon_data)[1]
        if x.endswith(".history")
    ]

    # Simple version. Anything updated recently (since startup?)
    # priority = sorted(all_cache, key=os.path.getmtime)
    # Sort by chance of it updating
    plays = utils.read_json(_playback_history_path, default={}).setdefault("plays", [])
    plays_for_type = [(time, t) for time, t in plays if t == media_type]
    priority = sorted(
        [
            (
                chance_playback_updates_widget(path, plays_for_type),
                utils.read_json(path).get("path", ""),
                path,
            )
            for path in all_cache
        ],
        reverse=True,
    )

    for chance, path, history_path in priority:
        hash = path2hash(path)
        last_update = xbmcvfs.Stat(history_path).st_mtime() - _startup_time
        if last_update < 0:
            utils.log(
                "widget not updated since startup {} {}".format(last_update, hash[:5]),
                "notice",
            )
        # elif chance < 0.3:
        #     log("chance widget changed after play {}% {}".format(chance, hash[:5]), 'notice')
        else:
            utils.log(
                "chance widget changed after play {}% {}".format(chance, hash[:5]),
                "notice",
            )
            yield hash, path


def chance_playback_updates_widget(history_path, plays, cutoff_time=60 * 5):
    cache_data = utils.read_json(history_path)
    history = cache_data.setdefault("history", [])
    # Complex version
    # - for each widget
    #    - come up with chance it will update after a playback
    #    - each pair of updates, is there a playback inbetween and updated with X min after playback
    #    - num playback with change / num playback with no change
    changes, non_changes, unrelated_changes = 0, 0, 0
    update = ""
    time_since_play = 0
    for play_time, media_type in plays:
        while True:
            last_update = update
            if not history:
                break
            update_time, update = history.pop(0)
            time_since_play = update_time - play_time
            # log("{} {} {} {}".format(update[:5],last_update[:5], unrelated_changes, time_since_play), 'notice')
            if time_since_play > 0:
                break
            elif update != last_update:
                unrelated_changes += 1

        if update == last_update:
            non_changes += 1
        elif (
            time_since_play > cutoff_time
        ):  # update too long after playback to be releated
            pass
        else:
            changes += 1
        # TODO: what if the previous update was a long time before playback?

    # There is probably a more statistically correct way of doing this but the idea is that
    # with few datapoints we should tend towards 0.5 probability but as we get more datapoints
    # then error goes down and rely on actual changes vs nonchanges
    # We will do a simple weighted average with 0.5 to simulate this
    # TODO: currently random widgets score higher than recently played widgets. need to score them lower
    # as they are less relevent
    utils.log(
        "changes={}, non_changes={}, unrelated_changes={}".format(
            changes, non_changes, unrelated_changes
        ),
        "debug",
    )
    datapoints = float(changes + non_changes)
    prob = changes / float(changes + non_changes + unrelated_changes)
    unknown_weight = 4
    prob = (prob * datapoints + 0.5 * unknown_weight) / (datapoints + unknown_weight)
    return prob


def save_playback_history(media_type, playback_percentage):
    # Record in json when things got played to help predict which widgets will change after playback
    # if playback_percentage < 0.7:
    #    return
    history = utils.read_json(_playback_history_path, default={})
    plays = history.setdefault("plays", [])
    plays.append((time.time(), media_type))
    utils.write_json(_playback_history_path, history)

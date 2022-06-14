import threading
import xbmcgui
import xbmcvfs
import xbmc

import glob
import hashlib
import json
import math
import os
import time
import random

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


def read_history(path, create_if_missing=True):
    hash = path2hash(path)
    history_path = os.path.join(_addon_data, "{}.history".format(hash))
    if not xbmcvfs.exists(history_path):
        if create_if_missing:
            cache_data = dict(history=[], widgets=[])
            utils.write_json(history_path, cache_data)
        else:
            cache_data = None
    else:
        cache_data = utils.read_json(history_path, default=dict(history=[], widgets=[]))
    return cache_data


def push_cache_queue(path, widget_id=None):
    hash = path2hash(path)
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

    command = {'jsonrpc': '2.0', 'method': 'JSONRPC.NotifyAll',
                'params': {'sender': "AutoWidget",
                    'message': "queue",
                    'data': (hash, path, widget_id),
                },
                'id': 1,}
    def send():
        while not utils.call_jsonrpc(command):
            xbmc.sleep(1000) # Wait untl service starts
    # Don't wait in case service hasn't started
    # TODO: check this doesn't still block until thread finishes
    threading.Thread(target=send).start()


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
    # if not is_cache_queue(hash):
    #     return []

    if notify is not None:
        widget_def = manage.get_widget_by_id(widget_id)
        if widget_def is not None:
            notify(widget_def.get("label", ""), path)

    new_files, files_changed = cache_files(path, widget_id)

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

    all_hist = [
        os.path.join(_addon_data, x)
        for x in xbmcvfs.listdir(_addon_data)[1]
        if x.endswith(".history")
    ]

    # Get rid of ones not read this session. These are old
    all_hist = [hist_path for hist_path in all_hist if (xbmcvfs.Stat(hist_path).st_mtime() - _startup_time) >= 0]

    # Simple version. Anything updated recently (since startup?)
    # priority = sorted(all_cache, key=os.path.getmtime)
    # Sort by chance of it updating
    plays = utils.read_json(_playback_history_path, default={}).setdefault("plays", [])
    plays_for_type = [(time, t) for time, t in plays if t == media_type or media_type is None]
    priority = sorted(
        [
            (
                chance_playback_updates_widget(cache_data, plays_for_type),
                cache_data.get("path", ""),
                hist_path,
            )
            for hist_path, cache_data in [(p, utils.read_json(p, default={})) for p in all_hist]
        ],
        reverse=True,
    )
    
    count_prob_changed = 0
    randoms = 0
    i = 0
    for chance, path, history_path in priority:
        hash = path2hash(path)
        if "page=" in path:
            # HACK: must be a better way
            continue
        elif chance >= 0.3 or i < 7:
            utils.log(
                "Queue {:.2f}% {} {}".format(chance * 100, hash[:5], path),
                "notice",
            )
            count_prob_changed += 1
            yield hash, path
        elif random.random() <= (1/len(priority)):
            # If widgets never get updated after playback we never get to know if they change after playback. So always pick some randomly
            utils.log("Queue random {:.2f}% {} {}".format(chance * 100, hash[:5], path), 'notice')
            randoms += 1
            yield hash, path
        else:
            utils.log("Prob not changes due to playback {:.2f}% {} {}".format(chance * 100, hash[:5], path), 'notice')
        i += 1
    utils.log("=== End Widget update: {} prob changed after playback {} randoms".format(count_prob_changed, randoms), 'notice')

def chance_playback_updates_widget(cache_data, plays, cutoff_time=60 * 60):
    history = cache_data.setdefault("history", [])
    hist_len = len(history)
    path = cache_data.get("path", "")
    # Complex version
    # - for each widget
    #    - come up with chance it will update after a playback
    #    - each pair of updates, is there a playback inbetween and updated with X min after playback
    #    - num playback with change / num playback with no change
    # C C P C C
    changes, non_changes, unrelated_changes, too_late_changes = 0, 0, 0, 0
    update = ""
    update_time = 0
    for play_time, media_type in plays:
        while (update_time - play_time) <= 0:
            last_update = update
            last_update_time = update_time
            if not history:
                break
            update_time, update = history.pop(0)
            # log("{} {} {} {}".format(update[:5],last_update[:5], unrelated_changes, time_since_play), 'notice')
            if (update_time - play_time) > 0:
                break
            elif update != last_update:
                # Update that happened with no play inbetween
                unrelated_changes += 1
        # We now have a update after a playback
        if not update_time:
            break
        elif not last_update:
            # haven't got to first update yet
            pass
        elif update == last_update:
            if update_time == last_update_time:
                # Two playbacks without any updates
                pass
            else:
                # Didn't change after playback
                non_changes += 1
        elif (update_time - play_time) <= cutoff_time:
            # Did change after playback
            changes += 1
        else:
            # update too long after playback to be releated
            too_late_changes += 1
            pass
            
        # TODO: what if the previous update was a long time before playback?

    # There is probably a more statistically correct way of doing this but the idea is that
    # with few datapoints we should tend towards 0.5 probability but as we get more datapoints
    # then error goes down and rely on actual changes vs nonchanges
    # We will do a simple weighted average with 0.5 to simulate this
    # TODO: currently random widgets score higher than recently played widgets. need to score them lower
    # as they are less relevent
    # HACK: could too late changes for now until we work out why
    datapoints = float(changes + too_late_changes + non_changes)
    all_changes = float(datapoints + unrelated_changes)
    if all_changes == 0:
        # we have no data or lost it. let's get it updated
        prob = 1.0
    else:
        prob = (changes) / all_changes
        unknown_weight = 4
        prob = (prob * datapoints + 0.5 * unknown_weight) / (datapoints + unknown_weight)

    utils.log(
        "prob:{:.2f}% changes:{} non_changes:{} non_play_changes:{} too_late:{} plays:{} hist:{}: {}".format(
            prob*100, changes, non_changes, unrelated_changes, too_late_changes, len(plays), hist_len, path,
        ),
        "notice",
    )
    return prob


def save_playback_history(media_type, playback_percentage, path):
    # Record in json when things got played to help predict which widgets will change after playback
    # if playback_percentage < 0.7:
    #    return
    history = utils.read_json(_playback_history_path, default={})
    plays = history.setdefault("plays", [])
    plays.append((time.time(), media_type))
    utils.write_json(_playback_history_path, history)

from resources.lib import refresh

if __name__ == "__main__":
    _monitor = refresh.RefreshService()
    _monitor.waitForAbort()

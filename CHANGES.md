## 0.4.2

- Fixes bug #52.  
  - Now worker's 'WaitForKill' thread is model specific (by adding model to the queue name).
- Cleaned up string handling in manager.
- Modified testing/test_full to test running multiple simultaneous models
- Modified models/test.sh to take sleep_count from input dir

## 0.4.1

Adds simple admin section to site secured by "admin_key"

- Bugs fixed: 
    - #41 Anyone or thing (i.e. bots) could kill jobs via jobs view page;  Now killing jobs links are exposed to admin section which can only be unlocked with key (/admin/YOUR_KEY)

## 0.4.0

Makes modelrunner more robust after load testing and usage showed some cracks.

- Worker now uses nginx as static server in production mode
- Primary pulls logs from worker on job completion to make workers truly ephemeral
- Added bash api for interaction with a modelrunner instance (testing/api_functions.sh)
- Added job queueing test
- Primary listener process no longer exits on error
- Bugs fixed:
    - #18 SimpleHTTPServer hangs; now use nginx on primary AND worker
    - #38 queued jobs skipped; not happening in testing
    - #39 killed jobs are now truly killed

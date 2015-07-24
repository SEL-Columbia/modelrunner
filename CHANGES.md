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

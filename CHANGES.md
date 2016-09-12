## 0.6.0
- Python 3 Support (#32)

## 0.5.2

- minor bug fix (#87) 

## 0.5.1

- Better support for Redis deployment to separate server

Closes #49

## 0.5.0

- Major Refactoring
  - standardized 'command' protocol between compute nodes
  - factored out 'dispatch' of command handlers
  - nodes now also listen on channels (for operational commands)
- Expose node status via /status and /status/refresh endpoints
- Python tests that can run via nose

Closes #42, #48, #63, and #68-75

## 0.4.7

- Fix kill bug #66

## 0.4.6

- Used QUEUED and KILLED status for jobs
- Allow Kill for QUEUED jobs

## 0.4.5

- Add json output for jobs endpoint

## 0.4.4

- Deployment geared more toward single model per worker
- Closes #57

## 0.4.3

- Support Sequencer v0.1.0
- Update bash api to handle zips from url

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

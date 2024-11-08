# Debug Notes - Dashboard Update Issues
Date: 2024-01-30

## Current Issue
Dashboard not updating properly and showing errors.

## Investigation Steps

1. Checked app.py configuration:
   - Found WebSocket using eventlet mode which has Windows compatibility issues
   - Error: `AttributeError: module 'ssl' has no attribute 'wrap_socket'`

2. Checked frontend implementation:
   - Using polling instead of WebSocket connections
   - Multiple polling intervals causing potential race conditions
   - Stats polling: 1 second
   - Trades polling: 5 seconds
   - Backend cache: 5 seconds

## Proposed Fix

1. Switch WebSocket configuration:
   ```python
   # Change from:
   socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
   
   # To:
   socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
   ```

2. Add proper host binding:
   ```python
   socketio.run(app, host='127.0.0.1', port=5000)
   ```

3. Update frontend to use WebSocket instead of polling

## Next Steps
1. Update app.py with new WebSocket configuration
2. Test connection stability
3. Monitor for any memory leaks with threading mode

## Notes
- Keep eventlet in requirements.txt for future Linux deployment options
- Threading mode is more stable on Windows for development
- Will need to monitor memory usage with threading mode

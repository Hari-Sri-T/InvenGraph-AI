// WebSocket connection and message handling for real-time updates

function initializeWebSocket(userId) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/ai/procurement/`;
    
    try {
        const socket = new WebSocket(wsUrl);
        
        socket.onopen = function(event) {
            console.log('WebSocket connected');
            socket.send(JSON.stringify({
                type: 'subscribe',
                user_id: userId,
            }));
        };
        
        socket.onmessage = function(event) {
            const message = JSON.parse(event.data);
            routeWebSocketMessage(message);
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket error:', error);
            showNotification('warning', 'Real-time updates unavailable');
        };
        
        socket.onclose = function(event) {
            console.log('WebSocket closed, reconnecting in 5 seconds...');
            setTimeout(() => initializeWebSocket(userId), 5000);
        };
        
        return socket;
    } catch (error) {
        console.error('Failed to initialize WebSocket:', error);
        return null;
    }
}

function routeWebSocketMessage(message) {
    switch (message.type) {
        case 'pipeline_status':
            handlePipelineStatusUpdate(message.data);
            break;
        case 'approval_request':
            handleNewApprovalRequest(message.data);
            break;
        case 'approval_response':
            handleApprovalResponse(message.data);
            break;
        case 'notification':
            showNotification(message.severity, message.message);
            break;
        default:
            console.warn('Unknown WebSocket message type:', message.type);
    }
}

function handlePipelineStatusUpdate(data) {
    // Dispatch custom event for pipeline status update
    window.dispatchEvent(new CustomEvent('pipeline:update', { detail: data }));
    
    // Update UI if on pipeline status page
    if (window.location.pathname.includes('/pipeline/') && typeof updatePipelineUI === 'function') {
        updatePipelineUI(data);
    }
}

function handleNewApprovalRequest(data) {
    // Show notification
    showNotification('info', `New approval request for ${data.part_name}`);
    
    // Update approval queue if visible
    window.dispatchEvent(new CustomEvent('approval:new', { detail: data }));
}

function handleApprovalResponse(data) {
    // Update approval queue
    window.dispatchEvent(new CustomEvent('approval:update', { detail: data }));
}

function subscribeToWebSocket(pipelineId) {
    if (App.state.socket && App.state.socket.readyState === WebSocket.OPEN) {
        App.state.socket.send(JSON.stringify({
            type: 'subscribe_pipeline',
            pipeline_id: pipelineId,
        }));
    }
}

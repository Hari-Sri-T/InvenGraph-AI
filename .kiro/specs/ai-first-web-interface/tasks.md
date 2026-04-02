# Implementation Plan: AI-First Web Interface

## Overview

This implementation plan creates a comprehensive web interface for the AI-First Logistics Management System using Django templates, HTMX, Alpine.js, and Tailwind CSS. The frontend connects to the existing AI Procurement backend (10 models, 7-node LangGraph pipeline, 4 agents) and positions AI as the central intelligence layer. The implementation follows a mobile-first, accessible design with real-time WebSocket updates and RESTful API integration.

## Tasks

- [x] 1. Set up Django app structure and configuration
  - Create ailms app structure with proper directories
  - Configure app in Django settings
  - Set up URL routing for all pages
  - Configure static files and templates directories
  - _Requirements: 20.1, 20.2, 24.1_

- [x] 2. Implement base template and layout system
  - [x] 2.1 Create base.html template with common structure
    - Implement HTML5 semantic structure (nav, main, footer)
    - Add Tailwind CSS CDN or compiled CSS
    - Include HTMX and Alpine.js libraries
    - Add meta tags for responsive design and accessibility
    - _Requirements: 15.1, 15.2, 15.3, 16.1, 20.2_
  
  - [x] 2.2 Create navigation component
    - Implement responsive navigation with hamburger menu for mobile
    - Add navigation links for all main pages
    - Include user authentication status display
    - Add skip navigation links for accessibility
    - _Requirements: 15.5, 15.6, 16.10_
  
  - [x] 2.3 Create notification toast component
    - Implement toast notification system with Alpine.js
    - Add support for success, error, warning, info severities
    - Implement auto-dismiss after 5 seconds
    - Add animation for slide-in effect
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10_


- [x] 3. Implement AI Dashboard page
  - [x] 3.1 Create dashboard view and URL route
    - Implement Django view to fetch dashboard data from API
    - Aggregate insights: active pipelines, pending approvals, forecast accuracy
    - Pass context data to template
    - _Requirements: 1.1, 1.2_
  
  - [x] 3.2 Create dashboard.html template
    - Display AI insights cards with metrics
    - Show predictions with part name, demand, confidence, trend
    - Display recommendations with priority and action links
    - Show recent activity timeline
    - _Requirements: 1.3, 1.4, 1.5_
  
  - [ ]* 3.3 Add real-time dashboard updates
    - Implement WebSocket subscription for dashboard metrics
    - Update metrics every 30 seconds without page reload
    - Handle WebSocket messages for dashboard updates
    - _Requirements: 1.6, 1.7, 9.1, 9.2, 9.3_

- [x] 4. Implement Parts Management page
  - [x] 4.1 Create parts list view and URL route
    - Implement Django view to fetch parts with AI insights
    - Include forecasted demand, confidence intervals, trend direction
    - Add search and filtering functionality
    - Implement pagination for large result sets
    - _Requirements: 2.1, 2.2, 2.4, 22.3_
  
  - [x] 4.2 Create parts_list.html template
    - Display parts catalog with search bar
    - Show part cards with stock levels and reorder points
    - Highlight parts below reorder point with visual indicators
    - Display AI insights: forecasted demand, days until stockout
    - Add "Trigger Procurement" button for each part
    - _Requirements: 2.3, 2.5_
  
  - [x] 4.3 Create part detail view and template
    - Implement Django view for single part details
    - Display full AI insights and supplier information
    - Show supplier rankings with reliability scores
    - Add procurement trigger button
    - _Requirements: 2.5, 2.6_
  
  - [x] 4.4 Implement procurement trigger functionality
    - Add HTMX POST request to trigger pipeline
    - Validate part has linked suppliers before triggering
    - Display success notification and redirect to pipeline status
    - Handle errors with user-friendly messages
    - _Requirements: 2.7, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 5. Implement Procurement Pipeline Viewer page
  - [x] 5.1 Create pipeline status view and URL route
    - Implement Django view to fetch pipeline status by ID
    - Fetch pipeline execution data including current node and status
    - Include node progress and outputs
    - _Requirements: 4.1_
  
  - [x] 5.2 Create pipeline_status.html template
    - Display pipeline ID, part name, status, trigger reason
    - Visualize 7-node workflow with progress indicators
    - Show current node and completion status for each node
    - Display node outputs when available
    - _Requirements: 4.2, 4.3_
  
  - [ ]* 5.3 Add real-time pipeline status updates
    - Implement WebSocket subscription for pipeline updates
    - Update node status and progress without page reload
    - Handle status changes: running, interrupted, completed, failed, rejected
    - Display link to approval request when status is interrupted
    - _Requirements: 4.4, 4.5, 9.3, 9.9_
  
  - [x] 5.4 Add error handling and retry functionality
    - Display error messages when pipeline fails
    - Show rejection reason when pipeline is rejected
    - Add retry button for failed pipelines
    - Display created PO ID when pipeline completes
    - _Requirements: 4.6, 4.7, 4.8, 18.1, 18.2, 18.3_

- [ ] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 7. Implement Approval Queue (HITL) page
  - [x] 7.1 Create approval queue view and URL route
    - Implement Django view to fetch pending approval requests
    - Filter by status (pending by default)
    - Include decision data, forecast data, and supplier rankings
    - Order by creation time (newest first)
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  
  - [x] 7.2 Create approval_queue.html template
    - Display pending approvals in card format
    - Show part name, pipeline ID, status badge
    - Display AI decision with reasoning and confidence level
    - Show forecast data with predicted demand and confidence interval
    - Display top 3 ranked suppliers with scores and pricing
    - _Requirements: 5.2, 5.3, 5.4_
  
  - [x] 7.3 Implement approval action functionality
    - Add approve, reject, modify buttons with Alpine.js
    - Implement modify modal for changing quantity or supplier
    - Validate user has approval permissions
    - Send POST request to approval action API endpoint
    - _Requirements: 5.5, 5.6, 5.7, 10.4, 10.5_
  
  - [x] 7.4 Add approval form validation
    - Validate approval request status is pending before submission
    - Validate modified quantity is positive number
    - Validate modified supplier ID exists
    - Display inline error messages for invalid input
    - _Requirements: 5.8, 12.4, 12.5_
  
  - [x] 7.5 Handle approval action responses
    - Update approval card status after action
    - Display success notification
    - Redirect to pipeline status page on approve/modify
    - Handle expired approvals gracefully
    - _Requirements: 5.9, 5.11, 18.4, 18.5_
  
  - [ ]* 7.6 Add real-time approval notifications
    - Implement WebSocket subscription for new approval requests
    - Display notification when new approval is created
    - Update approval queue without page reload
    - _Requirements: 5.10, 9.4, 9.5_

- [x] 8. Implement Supplier Management page
  - [x] 8.1 Create supplier list view and URL route
    - Implement Django view to fetch suppliers with AI scores
    - Include reliability metrics and AI evaluation scores
    - Order suppliers by overall AI score (descending)
    - _Requirements: 6.1, 6.5_
  
  - [x] 8.2 Create suppliers_list.html template
    - Display supplier catalog with search and filtering
    - Show supplier cards with name, description, active status
    - Display AI overall score prominently
    - Show reliability metrics: on-time delivery, quality acceptance, lead time accuracy
    - _Requirements: 6.1, 6.2_
  
  - [x] 8.3 Create supplier detail view and template
    - Implement Django view for single supplier details
    - Display all AI scores: overall, price, lead time, reliability
    - Show all parts supplied with pricing and lead times
    - Add supplier comparison functionality
    - _Requirements: 6.3, 6.4, 6.6_
  
  - [x] 8.4 Implement supplier comparison feature
    - Add checkbox selection for multiple suppliers
    - Create comparison modal with side-by-side metrics
    - Display all reliability and AI scores for comparison
    - _Requirements: 6.6_

- [x] 9. Implement Inventory Management page
  - [x] 9.1 Create inventory view and URL route
    - Implement Django view to fetch inventory data
    - Include AI optimization recommendations
    - Aggregate quantities across multiple locations
    - Generate alerts for low stock and stockout risks
    - _Requirements: 7.1, 7.6_
  
  - [x] 9.2 Create inventory.html template
    - Display parts with current stock levels
    - Show locations and quantities per location
    - Display total stock with minimum stock comparison
    - Highlight parts below minimum stock with visual indicators
    - _Requirements: 7.1, 7.3, 7.7_
  
  - [x] 9.3 Add AI optimization recommendations
    - Display recommended reorder point and minimum stock
    - Show adjustment reasoning from AI
    - Display forecast accuracy and stockout risk
    - Add visual comparison of current vs recommended values
    - _Requirements: 7.2, 7.5_
  
  - [x] 9.4 Implement inventory alerts
    - Generate low stock alerts with severity levels
    - Generate stockout risk alerts with severity levels
    - Display alerts prominently with color coding
    - _Requirements: 7.3, 7.4_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 11. Implement Analytics Dashboard page
  - [x] 11.1 Create analytics view and URL route
    - Implement Django view to fetch analytics data
    - Aggregate forecast accuracy overall and by category
    - Calculate procurement metrics: total pipelines, success rate, execution time
    - Fetch supplier performance data
    - Fetch demand trends with historical and forecasted data
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.8_
  
  - [x] 11.2 Create analytics.html template
    - Display forecast accuracy metrics with percentage
    - Show forecast accuracy by category in table format
    - Display procurement metrics in card format
    - Show supplier performance table with rankings
    - _Requirements: 8.1, 8.2, 8.4, 8.5_
  
  - [x] 11.3 Add data visualization with Chart.js
    - Implement forecast accuracy trend line chart
    - Create demand trends chart with historical and forecasted data
    - Add supplier performance comparison bar chart
    - Ensure charts are responsive and accessible
    - _Requirements: 8.3, 8.6, 8.7_

- [x] 12. Implement JavaScript API client module
  - [x] 12.1 Create api.js module for API interactions
    - Implement fetch wrapper with CSRF token handling
    - Add Content-Type header for JSON requests
    - Implement error handling with user-friendly messages
    - Add retry logic with exponential backoff (up to 3 retries)
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_
  
  - [x] 12.2 Add loading indicators and error recovery
    - Display loading spinner during API requests
    - Show "Try again" button when all retries fail
    - Display API response messages as notifications
    - Preserve UI state on errors
    - _Requirements: 11.7, 11.8, 11.9, 18.8_
  
  - [x] 12.3 Create API endpoint functions
    - Implement triggerProcurement(partId)
    - Implement fetchDashboardData()
    - Implement fetchPipelineStatus(pipelineId)
    - Implement fetchApprovals(status)
    - Implement processApproval(requestId, action, userData)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 4.1, 4.2, 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 13. Implement WebSocket real-time updates
  - [ ] 13.1 Create websocket.js module
    - Establish WebSocket connection on page load
    - Implement connection open handler with user subscription
    - Add message routing based on message type
    - Handle pipeline_status, approval_request, approval_response, notification messages
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [ ] 13.2 Add WebSocket error handling and reconnection
    - Implement error handler with user notification
    - Add automatic reconnection after 5 seconds on disconnect
    - Implement fallback to polling when WebSocket fails
    - Sync missed updates after reconnection
    - _Requirements: 9.7, 9.8, 18.6, 18.7_
  
  - [ ] 13.3 Create Django Channels WebSocket consumer
    - Implement WebSocket consumer in Python
    - Handle connect, disconnect, receive events
    - Implement user-specific subscriptions
    - Broadcast pipeline status updates to subscribed users
    - Broadcast approval notifications to users with permissions
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_
  
  - [ ] 13.4 Configure Django Channels routing
    - Set up ASGI application with Channels
    - Configure WebSocket URL routing
    - Set up Redis channel layer for message passing
    - _Requirements: 24.2, 24.4_

- [ ] 14. Implement form validation system
  - [ ] 14.1 Create validation.js module
    - Implement client-side validation functions
    - Add validation on blur and change events
    - Display inline error messages next to invalid fields
    - Prevent form submission with invalid data
    - _Requirements: 12.1, 12.2, 12.3_
  
  - [ ] 14.2 Add specific validation rules
    - Validate positive numbers for quantities
    - Validate required fields are not empty
    - Validate supplier IDs exist
    - Ensure client validation matches server validation
    - _Requirements: 12.4, 12.5, 12.6_
  
  - [ ] 14.3 Handle server-side validation errors
    - Display server error messages in UI
    - Preserve valid field values on error
    - Highlight fields with server-side errors
    - _Requirements: 12.7, 12.8_

- [ ] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 16. Implement authentication and authorization
  - [ ] 16.1 Add authentication middleware checks
    - Verify user is authenticated via Django session
    - Redirect unauthenticated users to login page
    - Add @login_required decorator to all views
    - _Requirements: 10.1, 10.2_
  
  - [ ] 16.2 Add permission checks for sensitive actions
    - Check procurement trigger permission before allowing trigger
    - Check approval permission before showing approval actions
    - Return HTTP 403 for unauthorized actions
    - Log permission denials for security audit
    - _Requirements: 10.3, 10.4, 10.5, 10.6, 25.5_
  
  - [ ] 16.3 Implement UI permission-based rendering
    - Hide or disable elements for unauthorized actions
    - Show/hide approval buttons based on permissions
    - Display appropriate messages for unauthorized users
    - _Requirements: 10.7_

- [ ] 17. Implement security measures
  - [ ] 17.1 Add CSRF protection
    - Include CSRF token in all POST, PUT, DELETE requests
    - Validate CSRF tokens on server side
    - Add CSRF token to HTMX requests
    - _Requirements: 17.1_
  
  - [ ] 17.2 Implement input sanitization
    - Sanitize user input to prevent XSS attacks
    - Use Django template auto-escaping for HTML output
    - Validate and sanitize all form inputs
    - _Requirements: 17.2, 20.5_
  
  - [ ] 17.3 Add rate limiting
    - Implement rate limiting of 100 requests per minute per user
    - Return HTTP 429 when rate limit exceeded
    - Display user-friendly rate limit message
    - _Requirements: 17.4_
  
  - [ ] 17.4 Configure secure connections
    - Use HTTPS for all HTTP traffic in production
    - Use WSS for all WebSocket traffic in production
    - Set HttpOnly, Secure, SameSite flags on cookies
    - _Requirements: 17.6, 17.7, 17.8_
  
  - [ ] 17.5 Implement error message sanitization
    - Sanitize error messages to prevent information leakage
    - Log detailed errors server-side only
    - Display generic error messages to users
    - _Requirements: 17.9_
  
  - [ ] 17.6 Add audit logging for approval actions
    - Log all approval actions with user ID and timestamp
    - Log action type (approve, reject, modify)
    - Store logs securely for compliance
    - _Requirements: 17.10, 25.1_

- [ ] 18. Implement caching strategy
  - [ ] 18.1 Add Redis caching for dashboard metrics
    - Cache dashboard metrics for 30 seconds
    - Implement cache key generation
    - Return cached data within 200ms
    - _Requirements: 21.1, 21.4_
  
  - [ ] 18.2 Add Redis caching for parts and suppliers
    - Cache parts list for 60 seconds
    - Cache supplier list for 60 seconds
    - Implement cache invalidation on data modification
    - _Requirements: 21.2, 21.3, 21.6_
  
  - [ ] 18.3 Implement cache fallback
    - Fall back to direct database queries when cache unavailable
    - Handle cache errors gracefully without breaking functionality
    - _Requirements: 21.7_

- [ ] 19. Optimize database queries
  - [ ] 19.1 Add query optimization for related objects
    - Use select_related for foreign key relationships
    - Use prefetch_related for reverse foreign keys and many-to-many
    - Optimize approval queue queries with related data
    - _Requirements: 22.1, 22.2_
  
  - [ ] 19.2 Implement pagination
    - Add pagination to parts list (20-50 items per page)
    - Add pagination to supplier list
    - Add pagination to approval queue
    - _Requirements: 22.3_
  
  - [ ] 19.3 Add database indexes
    - Verify indexes exist on frequently queried fields
    - Add indexes for pipeline status and created_at
    - Add indexes for approval status and expires_at
    - _Requirements: 22.4_
  
  - [ ] 19.4 Optimize API response times
    - Target response time of less than 500ms for dynamic data
    - Use database-level aggregation functions
    - Log slow queries for optimization review
    - _Requirements: 22.5, 22.6, 22.7_

- [ ] 20. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 21. Implement responsive design with Tailwind CSS
  - [ ] 21.1 Configure Tailwind CSS
    - Set up Tailwind CSS configuration file
    - Configure purge/content paths for production optimization
    - Add custom color scheme for AI branding
    - _Requirements: 14.3_
  
  - [ ] 21.2 Implement mobile-first layouts
    - Use single-column layout for viewport < 640px
    - Use tablet-optimized layout for 640px-1024px
    - Use desktop-optimized layout for > 1024px
    - _Requirements: 15.1, 15.2, 15.3_
  
  - [ ] 21.3 Add responsive navigation
    - Implement hamburger menu for mobile devices
    - Show full navigation links on desktop
    - Ensure minimum tap target size of 44x44 pixels on touch devices
    - _Requirements: 15.4, 15.5, 15.6_
  
  - [ ] 21.4 Ensure text scalability
    - Test text resize up to 200%
    - Maintain functionality without horizontal scrolling
    - Use relative units (rem, em) for font sizes
    - _Requirements: 15.7_

- [ ] 22. Implement accessibility features
  - [ ] 22.1 Add semantic HTML structure
    - Use semantic HTML5 elements (nav, main, article, aside)
    - Ensure proper heading hierarchy (h1-h6)
    - Use appropriate ARIA roles where needed
    - _Requirements: 16.1_
  
  - [ ] 22.2 Implement keyboard accessibility
    - Ensure all interactive elements are keyboard accessible
    - Implement logical tab order
    - Display visible focus indicators with 3:1 contrast ratio
    - _Requirements: 16.2, 16.3_
  
  - [ ] 22.3 Add ARIA labels and alt text
    - Provide alt text for all images and icons
    - Add ARIA labels for icon-only buttons
    - Use ARIA live regions for dynamic content updates
    - _Requirements: 16.4, 16.5_
  
  - [ ] 22.4 Ensure color contrast compliance
    - Verify 4.5:1 contrast ratio for normal text
    - Verify 3:1 contrast ratio for large text and components
    - Test with color contrast analyzer tools
    - _Requirements: 16.6, 16.7_
  
  - [ ] 22.5 Add accessible forms
    - Associate labels with inputs using for and id attributes
    - Use descriptive link text instead of generic phrases
    - Add skip navigation links for screen readers
    - _Requirements: 16.8, 16.9, 16.10_

- [ ] 23. Optimize page load performance
  - [ ] 23.1 Implement server-side rendering
    - Use Django templates for initial page content
    - Achieve First Contentful Paint < 1.5 seconds
    - Minimize time to interactive
    - _Requirements: 14.1, 14.5_
  
  - [ ] 23.2 Optimize static assets
    - Serve static assets with gzip or brotli compression
    - Ensure JavaScript bundle size < 100KB gzipped
    - Set appropriate cache headers for browser caching
    - _Requirements: 14.2, 14.3, 14.7_
  
  - [ ] 23.3 Implement responsive images
    - Use srcset for different screen sizes
    - Lazy load images below the fold
    - Optimize image file sizes
    - _Requirements: 14.4, 14.6_

- [ ] 24. Implement logging and monitoring
  - [ ] 24.1 Add approval action logging
    - Log all approval actions with user ID, timestamp, action type
    - Log approval request ID and pipeline ID
    - _Requirements: 25.1, 17.10_
  
  - [ ] 24.2 Add pipeline execution logging
    - Log pipeline start with trigger reason and user ID
    - Log pipeline completion with outcome and execution time
    - _Requirements: 25.2, 25.3_
  
  - [ ] 24.3 Add security event logging
    - Log authentication failures with timestamp and IP address
    - Log permission denials with user ID, action, timestamp
    - _Requirements: 25.4, 25.5_
  
  - [ ] 24.4 Add error logging
    - Log all errors with stack traces and context
    - Implement log retention policy
    - Send alerts for critical errors
    - _Requirements: 25.6, 25.7, 25.8_

- [ ] 25. Implement internationalization support
  - [ ] 25.1 Add Django translation functions
    - Use Django's translation functions for all user-facing text
    - Mark strings for translation with gettext
    - Create translation catalog
    - _Requirements: 23.1, 23.7_
  
  - [ ] 25.2 Add JavaScript translation support
    - Use Django's JavaScript catalog for client-side translations
    - Implement pluralization with blocktrans
    - _Requirements: 23.2, 23.3_
  
  - [ ] 25.3 Implement locale-aware formatting
    - Format dates and times according to user's locale
    - Format numbers according to user's locale
    - Support language preference changes without logout
    - _Requirements: 23.4, 23.5, 23.6_

- [ ] 26. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 27. Configure deployment infrastructure
  - [ ] 27.1 Set up WSGI and ASGI servers
    - Configure Gunicorn for Django WSGI application
    - Configure Daphne for WebSocket ASGI application
    - Set up process management with supervisord or systemd
    - _Requirements: 24.1, 24.2_
  
  - [ ] 27.2 Configure Nginx reverse proxy
    - Set up Nginx as reverse proxy for Django
    - Configure static file serving through Nginx
    - Set up WebSocket proxy pass configuration
    - _Requirements: 24.3_
  
  - [ ] 27.3 Configure Redis and PostgreSQL
    - Set up Redis for caching and WebSocket backend
    - Configure PostgreSQL connection pooling
    - Set up database backup strategy
    - _Requirements: 24.4, 24.5, 24.8_
  
  - [ ] 27.4 Configure SSL/TLS for production
    - Set up HTTPS with valid SSL certificates
    - Configure WSS for WebSocket connections
    - Enforce HTTPS redirects
    - _Requirements: 24.7_

- [ ] 28. Integration and wiring
  - [ ] 28.1 Wire all URL routes
    - Connect all views to URL patterns
    - Test all page navigation links
    - Verify URL reverse lookups work correctly
    - _Requirements: 20.6_
  
  - [ ] 28.2 Connect API endpoints to views
    - Verify all API calls from JavaScript reach correct views
    - Test CSRF token handling in all POST requests
    - Verify WebSocket connections establish correctly
    - _Requirements: 11.1, 17.1_
  
  - [ ] 28.3 Test end-to-end workflows
    - Test complete procurement trigger workflow
    - Test approval workflow from request to action
    - Test real-time updates across all pages
    - Verify data consistency across all layers
    - _Requirements: 19.1, 19.2, 19.3, 19.4, 19.5, 19.6, 19.7, 19.8, 19.9, 19.10_
  
  - [ ] 28.4 Verify error recovery mechanisms
    - Test pipeline failure and retry
    - Test approval expiration handling
    - Test WebSocket reconnection
    - Test API retry logic
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 18.8, 18.9_

- [ ] 29. Final integration checkpoint
  - Ensure all tests pass, verify all features work end-to-end, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- WebSocket tasks are optional but highly recommended for real-time experience
- Focus on core functionality first, then add real-time updates and optimizations
- All Python code should follow Django best practices and PEP 8 style guide
- All JavaScript code should be modular and maintainable
- All HTML templates should use Tailwind CSS utility classes
- Accessibility and security are non-negotiable requirements

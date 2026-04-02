# Implementation Plan: Agentic AI Inventory Management System

## Overview

This implementation plan transforms InvenTree's basic AI procurement feature into a fully autonomous, event-driven inventory management system. The system uses LangGraph for multi-agent orchestration, Prophet for demand forecasting, and Ollama (llama3) for intelligent decision-making. Implementation follows the design document's architecture with event-driven triggers, HITL approval gates, and continuous learning capabilities.

**Implementation Language:** Python 3.10+

**Key Technologies:** Django, LangGraph, Prophet, XGBoost, Ollama, PostgreSQL

**Approach:** Extend existing code in `src/backend/InvenTree/ai_procurement/` without breaking current functionality. Add new components incrementally, following the 6-phase roadmap from the design document.

## Tasks

- [-] 1. Foundation: Database Models and State Management
  - Create Django models for pipeline state persistence
  - Implement LangGraph state manager with PostgreSQL checkpointer
  - Set up basic pipeline structure
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 1.1 Create database models for pipeline execution tracking
  - Create `models.py` in `ai_procurement/` with PipelineExecution, DemandForecast, SupplierEvaluation, ProcurementDecisionLog, ApprovalRequest, ProcurementOutcome, ProphetModelCache, ReorderPointHistory, SupplierReliabilityScore, FewShotMemory models
  - Add UUID primary keys, JSONB fields for state_data, proper foreign keys to InvenTree models
  - Include validation rules from design document (e.g., scores between 0-1, non-negative quantities)
  - Add database indexes on part_id, status, created_at fields
  - _Requirements: 8.1, 8.2, 13.1, 13.2, 13.3, 13.4_

- [ ]* 1.2 Write property test for database model validation
  - **Property 5: Purchase Order Creation Atomicity**
  - **Validates: Requirements 6.1, 6.2, 6.4, 6.6**

- [x] 1.3 Create Django migrations for new models
  - Run `python manage.py makemigrations ai_procurement`
  - Review migration file for correctness
  - Test migration on development database
  - _Requirements: 8.1_

- [x] 1.4 Implement LangGraph state manager with PostgreSQL persistence
  - Create `state_manager.py` with StateManager class
  - Define PipelineState TypedDict with pipeline_id, part_id, current_node, agent_outputs, human_decision, status fields
  - Implement initialize_pipeline(), persist_checkpoint(), load_checkpoint() functions
  - Use LangGraph's PostgresSaver for state persistence
  - Implement interrupt_pipeline() and resume_pipeline() for HITL
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_


- [ ]* 1.5 Write property test for state persistence round-trip
  - **Property 1: Pipeline State Persistence Round-Trip**
  - **Validates: Requirements 8.1, 8.2, 8.4, 8.6**

- [x] 1.6 Define LangGraph workflow graph structure
  - Create `graph.py` with define_procurement_graph() function
  - Define nodes: data_collection, demand_forecasting, supplier_ranking, decision_making, human_approval, execution, learning_update
  - Define edges between nodes with conditional routing
  - Add interrupt_before on human_approval node
  - Configure PostgresSaver as checkpointer
  - _Requirements: 8.1, 8.2, 5.1_

- [ ] 1.7 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 2. Event-Driven Pipeline Triggering
  - Implement Django signal handlers for stock changes
  - Create event bus for pipeline triggering
  - Add event deduplication logic
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2.1 Create signal handler for StockItem changes
  - Create `signals.py` in `ai_procurement/`
  - Implement on_stock_change() handler connected to StockItem post_save signal
  - Calculate total stock for part and compare to reorder point (Part.minimum_stock)
  - Create pipeline trigger event if stock below reorder point
  - _Requirements: 1.1, 1.2, 15.1_

- [x] 2.2 Implement event deduplication to prevent duplicate triggers
  - Add event queue with 60-second deduplication window
  - Use Redis or in-memory cache to track recent events per part
  - Only trigger pipeline if no event for same part in last 60 seconds
  - _Requirements: 1.4_

- [ ]* 2.3 Write property test for event deduplication
  - **Property 10: Event Deduplication**
  - **Validates: Requirements 1.4**

- [x] 2.4 Add signal handler for SalesOrderLineItem creation
  - Connect to SalesOrderLineItem post_save signal
  - Calculate projected stock after order fulfillment
  - Trigger pipeline if projected stock will fall below reorder point
  - _Requirements: 1.5_

- [x] 2.5 Create async task queue for pipeline execution
  - Set up Celery or Django-Q for background task processing
  - Create run_pipeline_async() task that calls LangGraph
  - Configure task queue workers in Docker Compose
  - _Requirements: 1.3_

- [x] 2.6 Register signal handlers in Django app config
  - Update `apps.py` to register signals on app ready
  - Test signal triggering with StockItem.save()
  - _Requirements: 1.1, 15.1_


- [ ] 2.7 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 3. Demand Agent: Prophet Forecasting
  - Implement demand forecasting with Prophet
  - Add XGBoost fallback for insufficient data
  - Implement model caching for performance
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

- [x] 3.1 Create Demand Agent with historical data collection
  - Create `agents/demand_agent.py` with DemandAgent class
  - Implement get_historical_consumption() to query StockItemTracking, SalesOrderLineItem, Build models
  - Transform data to Prophet format (ds: date, y: consumption)
  - Handle missing dates by filling with 0 consumption
  - Limit lookback to 180 days for performance
  - _Requirements: 2.1, 15.2, 15.3, 15.4_

- [x] 3.2 Implement Prophet model training and forecasting
  - Implement train_prophet_model() with daily and weekly seasonality
  - Implement forecast_demand() that generates 30-day forecast
  - Calculate confidence intervals (yhat_lower, yhat_upper)
  - Detect seasonality patterns and trend direction
  - Ensure predicted demand is always non-negative
  - _Requirements: 2.2, 2.5, 2.6, 2.9_

- [ ]* 3.3 Write property test for forecast non-negativity
  - **Property 2: Forecast Non-Negativity**
  - **Validates: Requirements 2.9**

- [ ]* 3.4 Write property test for confidence interval ordering
  - **Property 7: Forecast Confidence Interval Ordering**
  - **Validates: Requirements 2.5**

- [x] 3.5 Implement Prophet model caching with 7-day TTL
  - Implement cache_prophet_model() to serialize and store model in ProphetModelCache table
  - Implement get_cached_prophet_model() to retrieve and deserialize model
  - Check model age and use cached model if less than 7 days old
  - _Requirements: 2.7, 2.8_

- [ ]* 3.6 Write property test for Prophet model caching
  - **Property 12: Prophet Model Caching**
  - **Validates: Requirements 2.7, 2.8**

- [x] 3.7 Implement XGBoost fallback for insufficient data
  - Implement forecast_with_xgboost() for when Prophet fails
  - Use simple moving average if data < 14 days
  - Set model_used field appropriately in ForecastResult
  - _Requirements: 2.3, 2.4_

- [x] 3.8 Calculate forecast accuracy metrics
  - Implement calculate_forecast_accuracy() using historical forecasts
  - Calculate MAPE (Mean Absolute Percentage Error)
  - Store accuracy score in ForecastResult
  - _Requirements: 2.2_


- [x] 3.9 Integrate Demand Agent into LangGraph pipeline
  - Add demand_forecasting node to graph
  - Connect to data_collection node
  - Store ForecastResult in pipeline state
  - _Requirements: 2.1, 2.2_

- [ ] 3.10 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Supplier Agent: Multi-Criteria Ranking
  - Implement supplier ranking with configurable weights
  - Calculate price, lead time, and reliability scores
  - Check MOQ constraints
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9_

- [x] 4.1 Create Supplier Agent with multi-criteria scoring
  - Create `agents/supplier_agent.py` with SupplierAgent class
  - Implement rank_suppliers() to query SupplierPart relationships
  - Define CriteriaWeights with configurable price_weight (0.4), lead_time_weight (0.3), reliability_weight (0.3)
  - _Requirements: 3.1, 3.2, 15.5_

- [x] 4.2 Implement price score normalization
  - Calculate unit_price for each supplier (handle quantity breaks)
  - Normalize price scores: higher score for lower prices
  - Handle edge case where all suppliers have same price
  - _Requirements: 3.2, 3.3_

- [x] 4.3 Implement lead time score normalization
  - Get lead_time_days from SupplierPart (default 30 if NULL)
  - Normalize lead time scores: higher score for shorter lead times
  - Handle edge case where all suppliers have same lead time
  - _Requirements: 3.2, 3.4_

- [x] 4.4 Implement reliability score integration
  - Implement get_supplier_reliability() to query SupplierReliabilityScore table
  - Use default reliability score of 0.5 if no historical data
  - _Requirements: 3.2, 3.5_

- [x] 4.5 Implement MOQ constraint checking
  - Check minimum_order_quantity from SupplierPart
  - Set moq_met flag based on required_quantity >= MOQ
  - _Requirements: 3.6_

- [x] 4.6 Calculate overall weighted scores and rank suppliers
  - Calculate overall_score as weighted sum of price, lead time, reliability
  - Sort suppliers by overall_score descending
  - Assign ranking_position starting from 1
  - Generate recommendation_reason for each supplier
  - _Requirements: 3.2, 3.7, 3.8_

- [ ]* 4.7 Write property test for supplier score normalization
  - **Property 3: Supplier Score Normalization**
  - **Validates: Requirements 3.2, 3.9**

- [ ]* 4.8 Write property test for supplier ranking consistency
  - **Property 8: Supplier Ranking Consistency**
  - **Validates: Requirements 3.7, 3.8**


- [x] 4.9 Integrate Supplier Agent into LangGraph pipeline
  - Add supplier_ranking node to graph
  - Connect to demand_forecasting node
  - Store List[SupplierRanking] in pipeline state
  - Handle error case when no suppliers found
  - _Requirements: 3.1, 9.4_

- [ ] 4.10 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Decision Agent: LLM-Based Reasoning
  - Implement Ollama integration for decision-making
  - Build comprehensive LLM prompts with context
  - Add rule-based fallback for LLM failures
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9_

- [x] 5.1 Set up Ollama integration and connection
  - Create `agents/decision_agent.py` with DecisionAgent class
  - Implement call_ollama() to POST to http://host.docker.internal:11434/api/generate
  - Use llama3 model with temperature=0.3, format="json"
  - Set 45-second timeout
  - _Requirements: 4.3, 15.3_

- [x] 5.2 Implement LLM prompt construction with few-shot examples
  - Implement build_llm_prompt() that includes part data, forecast, top 3 suppliers
  - Retrieve few-shot examples from FewShotMemory based on part category
  - Format prompt to request JSON output with decision, quantity, supplier_id, reasoning, confidence_level, risk_factors, alternative_actions
  - _Requirements: 4.1, 4.2_

- [x] 5.3 Implement LLM response parsing and validation
  - Implement parse_llm_output() to extract JSON from Ollama response
  - Validate required fields: decision, quantity, reasoning
  - Handle invalid JSON with regex extraction fallback
  - _Requirements: 4.4_

- [x] 5.4 Implement rule-based fallback decision logic
  - Implement make_rule_based_decision() for when LLM fails
  - Calculate projected_stock = current_stock - forecasted_demand
  - Order if projected_stock < minimum_stock * 1.2 (safety buffer)
  - Select top-ranked supplier
  - Set confidence_level="medium" and add "LLM unavailable" to risk_factors
  - _Requirements: 4.5, 4.6, 9.1_

- [ ]* 5.5 Write property test for decision value validity
  - **Property 9: Decision Value Validity**
  - **Validates: Requirements 4.7, 4.8**

- [ ]* 5.6 Write property test for LLM fallback behavior
  - **Property 11: LLM Fallback Behavior**
  - **Validates: Requirements 4.5, 4.6, 9.1**

- [x] 5.7 Implement prompt sanitization for security
  - Sanitize all user-provided data before including in prompts
  - Escape special characters that could manipulate LLM
  - Validate LLM output against business rules
  - _Requirements: 11.2_


- [x] 5.8 Integrate Decision Agent into LangGraph pipeline
  - Add decision_making node to graph
  - Connect to supplier_ranking node
  - Store ProcurementDecision in pipeline state
  - Log decision to ProcurementDecisionLog table
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 5.9 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Human-in-the-Loop Approval Gate
  - Implement LangGraph interrupt for human approval
  - Create notification service for in-app and email alerts
  - Build approval response handling
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9_

- [x] 6.1 Implement approval gate with LangGraph interrupt
  - Create `approval_gate.py` with ApprovalGate class
  - Implement create_approval_request() to create ApprovalRequest record
  - Add human_approval node to LangGraph with interrupt_before
  - Persist pipeline state when interrupted
  - _Requirements: 5.1, 5.2, 8.2_

- [ ]* 6.2 Write property test for approval gate blocking
  - **Property 4: Approval Gate Blocking**
  - **Validates: Requirements 5.1, 5.9**

- [x] 6.3 Create notification service for in-app notifications
  - Create `notifications.py` with NotificationService class
  - Implement send_in_app_notification() using InvenTree's notification system
  - Format notification with part name, forecast, supplier, reasoning
  - Determine responsible users from Part.responsible_owner
  - _Requirements: 5.3, 12.1, 12.3, 12.4_

- [x] 6.4 Implement email notification delivery
  - Implement send_email_notification() using Django's email backend
  - Send emails asynchronously to prevent blocking
  - Include approval URL with signed token
  - Handle email delivery failures gracefully
  - _Requirements: 5.4, 12.2, 12.5_

- [x] 6.5 Implement approval timeout handling
  - Add expires_at field to ApprovalRequest (default 7 days)
  - Create periodic task to check for expired requests
  - Mark expired requests as "expired" and reject pipeline
  - _Requirements: 5.8_

- [x] 6.6 Implement approval response processing
  - Implement process_approval() to handle approve/reject/modify actions
  - Verify user has "purchase_order.add" permission
  - Log approval action with user_id, timestamp, IP address
  - Resume pipeline with human decision
  - _Requirements: 5.5, 5.6, 5.7, 11.1, 11.6_


- [x] 6.7 Implement pipeline resume after approval
  - Implement resume_pipeline_after_approval() in state_manager.py
  - Load persisted state from PostgreSQL
  - Update state with human decision
  - Continue to execution node if approved/modified
  - Mark pipeline as rejected if rejected
  - _Requirements: 5.5, 5.6, 5.7, 8.3, 8.4, 8.5_

- [ ]* 6.8 Write property test for pipeline state persistence at transitions
  - **Property 13: Pipeline State Persistence at Transitions**
  - **Validates: Requirements 8.1, 8.2**

- [ ] 6.9 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Execution Agent: Purchase Order Creation
  - Implement PurchaseOrder creation with atomic transactions
  - Add metadata linking to pipeline execution
  - Handle creation failures with rollback
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 7.1 Create Execution Agent for PO creation
  - Create `agents/execution_agent.py` with ExecutionAgent class
  - Implement create_purchase_order() to create PurchaseOrder with status=10 (Pending)
  - Add PurchaseOrderLineItem with approved quantity
  - Store pipeline metadata (pipeline_id, approval_request_id) in PO
  - _Requirements: 6.1, 6.2, 6.3, 15.4_

- [x] 7.2 Implement atomic transaction handling
  - Wrap PO creation in Django transaction.atomic()
  - Ensure both PO and line item created or neither exists
  - Roll back on any validation error
  - _Requirements: 6.4, 6.6_

- [ ]* 7.3 Write property test for PO creation atomicity
  - **Property 5: Purchase Order Creation Atomicity**
  - **Validates: Requirements 6.1, 6.2, 6.4, 6.6**

- [x] 7.4 Implement error handling and retry logic
  - Handle validation errors with clear error messages
  - Log creation failures with full context
  - Notify users of creation failures
  - _Requirements: 6.4, 9.6_

- [x] 7.5 Integrate Execution Agent into LangGraph pipeline
  - Add execution node to graph
  - Connect to human_approval node (after resume)
  - Store po_id in pipeline state
  - Trigger learning layer update after successful creation
  - _Requirements: 6.1, 6.5_

- [ ] 7.6 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 8. Learning Layer: Continuous Improvement
  - Implement outcome logging and Prophet retraining
  - Add EMA trend calculation and reorder point adjustment
  - Implement supplier reliability scoring
  - Build few-shot memory for LLM context
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_

- [x] 8.1 Create Learning Layer with outcome logging
  - Create `learning/learning_layer.py` with LearningLayer class
  - Implement log_outcome() to create ProcurementOutcome record
  - Link outcome to pipeline execution
  - Store forecast_demand, quantity_ordered, supplier_used
  - _Requirements: 7.1, 6.5, 13.6_

- [x] 8.2 Implement Prophet model retraining
  - Implement retrain_prophet_model() to train new model with latest data
  - Schedule retraining asynchronously using Celery/Django-Q
  - Serialize and cache new model in ProphetModelCache
  - Increment model version number
  - _Requirements: 7.2, 7.3_

- [x] 8.3 Implement EMA trend calculation
  - Implement update_ema_trends() to calculate exponential moving average
  - Use alpha=0.3 for smoothing factor
  - Update EMA with recent consumption data (last 7 days)
  - Store trend metrics in database
  - _Requirements: 7.4_

- [x] 8.4 Implement reorder point adjustment logic
  - Implement adjust_reorder_point() based on forecast accuracy
  - Increase reorder point by 20% if accuracy < 0.7 or stockouts > 2 in 90 days
  - Decrease reorder point by 10% if accuracy > 0.9 and no stockouts in 90 days
  - Bound adjustments: new value between 0 and 10x current value
  - Update Part.minimum_stock field
  - Log adjustment in ReorderPointHistory
  - _Requirements: 7.5, 7.6, 7.9_

- [ ]* 8.5 Write property test for reorder point adjustment bounds
  - **Property 6: Reorder Point Adjustment Bounds**
  - **Validates: Requirements 7.5, 7.6, 7.9**

- [x] 8.6 Implement supplier reliability scoring
  - Implement update_supplier_reliability() to calculate on-time delivery rate
  - Calculate quality_acceptance_rate and lead_time_accuracy
  - Update SupplierReliabilityScore table
  - Use 90-day calculation period
  - _Requirements: 7.7_

- [x] 8.7 Implement few-shot memory storage
  - Implement store_few_shot_example() to save quality examples
  - Evaluate outcome quality based on forecast error, delivery performance, stockouts
  - Only store examples with "excellent" or "good" outcomes
  - Link examples to part category for retrieval
  - _Requirements: 7.8_


- [x] 8.8 Implement actual demand tracking and forecast error calculation
  - Create periodic task to update ProcurementOutcome with actual_demand
  - Calculate actual consumption between order date and forecast period end
  - Calculate forecast_error = ABS(forecast_demand - actual_demand)
  - Update delivery_on_time based on PO completion date
  - _Requirements: 7.1, 13.6_

- [x] 8.9 Integrate Learning Layer into LangGraph pipeline
  - Add learning_update node to graph
  - Connect to execution node
  - Call log_outcome() after PO creation
  - Schedule async tasks for retraining and adjustments
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 8.10 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. API Endpoints and Views
  - Create REST API endpoints for pipeline management
  - Add endpoints for approval actions
  - Implement pipeline status queries
  - _Requirements: 5.5, 5.6, 5.7, 15.5_

- [x] 9.1 Update existing views.py with new endpoints
  - Keep existing ProcurementRunView and ProcurementApproveView for backward compatibility
  - Add deprecation warnings to old endpoints
  - _Requirements: 15.4_

- [x] 9.2 Create API endpoint for manual pipeline triggering
  - Add PipelineTriggerView to manually start pipeline for a part
  - Verify user permissions
  - Return pipeline_id and status
  - _Requirements: 1.2_

- [x] 9.3 Create API endpoint for approval actions
  - Add ApprovalActionView to handle approve/reject/modify
  - Verify user has "purchase_order.add" permission
  - Call resume_pipeline_after_approval()
  - Return updated pipeline status
  - _Requirements: 5.5, 5.6, 5.7, 11.1_

- [x] 9.4 Create API endpoint for pipeline status queries
  - Add PipelineStatusView to get current pipeline state
  - Return pipeline status, current node, agent outputs
  - Filter by part_id or pipeline_id
  - _Requirements: 8.1, 8.2_

- [x] 9.5 Create API endpoint for approval request listing
  - Add ApprovalRequestListView to get pending approvals
  - Filter by user (responsible_owner)
  - Include forecast summary and supplier rankings
  - _Requirements: 5.3, 12.1_

- [x] 9.6 Add URL routing for new endpoints
  - Update `urls.py` to register new views
  - Use RESTful URL patterns
  - _Requirements: 15.5_


- [ ] 9.7 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. InvenTree Plugin UI Integration
  - Create React/TypeScript components for approval interface
  - Add forecast visualization charts
  - Implement supplier comparison table
  - _Requirements: 5.3, 12.1, 12.4, 15.5_

- [x] 10.1 Extend existing AIProcurementPanel.tsx with approval UI
  - Add ApprovalRequestCard component to display pending approvals
  - Show part name, forecasted demand, recommended supplier, AI reasoning
  - Add approve/reject/modify buttons
  - _Requirements: 5.3, 12.4_

- [ ] 10.2 Create forecast visualization component
  - Add ForecastChart component using Chart.js or Recharts
  - Display historical consumption and predicted demand
  - Show confidence intervals as shaded area
  - Highlight seasonality patterns
  - _Requirements: 12.4_

- [x] 10.3 Create supplier comparison table component
  - Add SupplierComparisonTable component
  - Display top 3 suppliers with scores, prices, lead times
  - Highlight recommended supplier
  - Show MOQ constraints
  - _Requirements: 12.4_

- [x] 10.4 Implement approval action handlers
  - Add handleApprove(), handleReject(), handleModify() functions
  - Call ApprovalActionView API endpoint
  - Show success/error notifications
  - Refresh approval list after action
  - _Requirements: 5.5, 5.6, 5.7_

- [x] 10.5 Add pipeline status indicator
  - Create PipelineStatusBadge component
  - Show current pipeline status (running, interrupted, completed, failed)
  - Display current node in pipeline
  - _Requirements: 8.1_

- [ ] 10.6 Integrate plugin UI with InvenTree part detail page
  - Register plugin panel in InvenTree plugin system
  - Add panel to part detail page
  - Test UI rendering and interactions
  - _Requirements: 15.5_

- [ ] 10.7 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 11. Configuration and Settings
  - Add configurable parameters for system tuning
  - Create settings file for weights, timeouts, thresholds
  - Implement configuration validation
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

- [x] 11.1 Create configuration file for system parameters
  - Create `config.py` with default values for all configurable parameters
  - Include supplier ranking weights (price: 0.4, lead_time: 0.3, reliability: 0.3)
  - Include forecast horizon (default 30 days)
  - Include approval timeout (default 7 days)
  - Include EMA smoothing factor (alpha: 0.3)
  - Include Prophet model cache TTL (default 7 days)
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [x] 11.2 Implement configuration parameter validation
  - Validate weights sum to 1.0
  - Validate forecast horizon > 0
  - Validate timeout > 0
  - Validate alpha between 0 and 1
  - Validate TTL > 0
  - _Requirements: 14.7_

- [x] 11.3 Add environment variable overrides
  - Allow configuration via environment variables
  - Use format: AI_PROCUREMENT_PRICE_WEIGHT, AI_PROCUREMENT_FORECAST_DAYS, etc.
  - Document all environment variables
  - _Requirements: 14.6_

- [x] 11.4 Update agents to use configuration parameters
  - Update SupplierAgent to use configured weights
  - Update DemandAgent to use configured forecast horizon and cache TTL
  - Update ApprovalGate to use configured timeout
  - Update LearningLayer to use configured alpha
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [ ]* 11.5 Write property test for configuration parameter usage
  - **Property 16: Configuration Parameter Usage**
  - **Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5**

- [ ] 11.6 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Error Handling and Logging
  - Implement comprehensive error handling for all agents
  - Add structured logging for debugging
  - Create error notification system
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

- [x] 12.1 Implement error handling in Demand Agent
  - Catch Prophet training failures and fall back to XGBoost
  - Catch insufficient data errors and use simple moving average
  - Log all errors with full context (part_id, data characteristics)
  - _Requirements: 9.2, 9.3_


- [x] 12.2 Implement error handling in Supplier Agent
  - Raise clear exception when no suppliers found
  - Provide actionable error message: "Please add suppliers for this part"
  - Send notification to responsible users
  - _Requirements: 9.4_

- [x] 12.3 Implement error handling in Decision Agent
  - Catch Ollama connection failures and fall back to rule-based logic
  - Catch JSON parsing errors and attempt regex extraction
  - Log LLM errors with prompt and response
  - _Requirements: 9.1, 9.7_

- [ ] 12.4 Implement error handling in Execution Agent
  - Catch validation errors during PO creation
  - Roll back transaction on any error
  - Log detailed error with validation messages
  - Send notification to users with error details
  - _Requirements: 9.6_

- [ ] 12.5 Implement database connection error handling
  - Catch database connection errors
  - Attempt to persist last known state
  - Mark pipeline as failed
  - Log error with full stack trace
  - _Requirements: 9.5_

- [x] 12.6 Add structured logging throughout system
  - Use Python logging module with INFO level for normal operations
  - Use DEBUG level for detailed troubleshooting
  - Log all pipeline transitions with pipeline_id, part_id, node
  - Log all agent outputs with timing information
  - Never log sensitive data (passwords, API keys)
  - _Requirements: 9.8, 11.8_

- [x] 12.7 Create error notification system
  - Implement send_error_notification() to alert users of failures
  - Include error message, pipeline_id, part_id
  - Send via in-app notification and email
  - _Requirements: 9.4, 9.6_

- [ ] 12.8 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Security Implementation
  - Implement authentication and authorization checks
  - Add prompt sanitization for LLM security
  - Implement secure token generation for approval URLs
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8_

- [ ] 13.1 Implement permission checks for approval actions
  - Verify user has "purchase_order.add" permission before approval
  - Use Django's permission system
  - Return 403 Forbidden if permission denied
  - _Requirements: 11.1_

- [ ]* 13.2 Write property test for authorization check
  - **Property 17: Authorization Check**
  - **Validates: Requirements 11.1**


- [ ] 13.3 Implement prompt sanitization for LLM security
  - Sanitize all user-provided data before including in prompts
  - Escape special characters that could manipulate LLM
  - Validate LLM output against business rules
  - Never execute LLM-generated code
  - _Requirements: 11.2_

- [ ]* 13.4 Write property test for prompt sanitization
  - **Property 18: Prompt Sanitization**
  - **Validates: Requirements 11.2**

- [ ] 13.5 Implement secure approval URL generation
  - Use Django's signing module to create signed tokens
  - Include pipeline_id and approval_request_id in token
  - Set token expiration to match approval timeout (7 days)
  - Verify token signature before allowing approval
  - _Requirements: 11.5_

- [ ] 13.6 Implement audit logging for all approval actions
  - Log user_id, timestamp, IP address for all approvals
  - Log action (approve/reject/modify) and any modifications
  - Store logs in separate audit table
  - _Requirements: 11.6_

- [ ] 13.7 Implement SQL injection prevention
  - Use Django ORM for all database queries (no raw SQL)
  - Validate all user inputs
  - Use parameterized queries if raw SQL is necessary
  - _Requirements: 11.7_

- [ ] 13.8 Implement Ollama API security
  - Ensure Ollama runs on localhost or internal network only
  - Use Docker network isolation
  - Implement request timeouts (45 seconds)
  - Rate limit LLM calls per part (max 1 per minute)
  - _Requirements: 11.3_

- [ ] 13.9 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Performance Optimization
  - Implement database query optimization
  - Add caching for frequently accessed data
  - Optimize LLM prompt size
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

- [ ] 14.1 Add database indexes for performance
  - Add index on PipelineExecution (part_id, status, created_at)
  - Add index on DemandForecast (part_id, created_at)
  - Add index on SupplierEvaluation (supplier_id, part_id)
  - Add index on ApprovalRequest (status, expires_at)
  - Add composite index on SupplierReliabilityScore (supplier_id, part_id)
  - _Requirements: 10.5_


- [ ] 14.2 Optimize historical data queries
  - Limit lookback to 180 days for Prophet training
  - Use database aggregation instead of Python loops
  - Add select_related() and prefetch_related() for foreign keys
  - _Requirements: 10.1, 10.2_

- [ ] 14.3 Implement supplier reliability score caching
  - Cache reliability scores with 24-hour TTL
  - Use Redis or Django cache framework
  - Invalidate cache when new delivery data arrives
  - _Requirements: 10.3_

- [ ] 14.4 Optimize LLM prompt size
  - Limit prompt to essential context only
  - Include only top 3 suppliers (not all)
  - Limit few-shot examples to 3 most relevant
  - Use temperature=0.3 for faster responses
  - _Requirements: 10.4_

- [ ] 14.5 Implement async notification delivery
  - Send email notifications asynchronously using Celery/Django-Q
  - Create in-app notifications immediately (synchronous)
  - Don't block pipeline execution on email delivery
  - _Requirements: 10.6_

- [ ] 14.6 Optimize checkpoint persistence
  - Persist only at node transitions (not every operation)
  - Use JSONB for efficient state storage
  - Batch multiple state updates in single transaction
  - _Requirements: 10.5_

- [ ] 14.7 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 15. Integration Testing
  - Create end-to-end integration tests
  - Test pipeline recovery after restart
  - Test concurrent pipeline execution
  - Test learning layer feedback loop
  - _Requirements: All requirements_

- [ ] 15.1 Create end-to-end pipeline execution test
  - Test complete flow: trigger → forecast → rank → decide → approve → execute → learn
  - Verify all agent outputs stored in state
  - Verify PurchaseOrder created successfully
  - Verify learning layer updated
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1_

- [ ]* 15.2 Write property test for pipeline recovery after restart
  - **Property 19: Pipeline Recovery After Restart**
  - **Validates: Requirements 8.3, 8.5**

- [ ] 15.3 Create concurrent pipeline execution test
  - Trigger pipelines for 10 parts simultaneously
  - Verify no state interference between pipelines
  - Verify all pipelines complete successfully
  - Verify database consistency
  - _Requirements: 10.6_


- [ ] 15.4 Create learning layer feedback loop test
  - Execute pipeline and create PO
  - Simulate delivery and consumption
  - Verify Prophet model retrained
  - Verify reorder point adjusted
  - Execute new pipeline for same part
  - Verify improved forecast accuracy
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [ ]* 15.5 Write property test for learning layer outcome logging
  - **Property 20: Learning Layer Outcome Logging**
  - **Validates: Requirements 7.1, 6.5**

- [ ] 15.6 Create error recovery scenario tests
  - Test Ollama unavailable scenario
  - Test database connection loss
  - Test invalid supplier data
  - Verify graceful degradation
  - Verify error notifications sent
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

- [ ] 15.7 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Documentation and Deployment
  - Create user documentation
  - Write developer documentation
  - Prepare deployment configuration
  - _Requirements: All requirements_

- [ ] 16.1 Create user documentation
  - Document how to configure system parameters
  - Document approval workflow for procurement managers
  - Document how to interpret forecast visualizations
  - Document how to handle error notifications
  - Create troubleshooting guide

- [ ] 16.2 Create developer documentation
  - Document architecture and component interactions
  - Document database schema and models
  - Document API endpoints and request/response formats
  - Document how to add new agents or modify existing ones
  - Document testing strategy and how to run tests

- [ ] 16.3 Create deployment configuration
  - Update Docker Compose with Ollama service
  - Configure PostgreSQL for state persistence
  - Configure Celery/Django-Q for async tasks
  - Configure SMTP for email notifications
  - Document environment variables

- [ ] 16.4 Create database migration guide
  - Document how to run migrations
  - Document how to seed initial data
  - Document how to backup and restore data

- [ ] 16.5 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [ ] 17. Data Seeding and Demo Preparation
  - Seed database with Inventory Optimisation Dataset
  - Create demo parts with realistic data
  - Configure demo environment
  - _Requirements: All requirements_

- [ ] 17.1 Create data seeding script for historical consumption
  - Create `management/commands/seed_inventory_data.py` Django command
  - Load Inventory Optimisation Dataset CSV
  - Create StockItemTracking records for 180 days of history
  - Create realistic consumption patterns with seasonality

- [ ] 17.2 Create demo parts with supplier relationships
  - Create 10-20 demo parts in various categories
  - Link each part to 2-5 suppliers with different prices and lead times
  - Set realistic minimum_stock values (reorder points)
  - Assign responsible_owner to demo users

- [ ] 17.3 Seed supplier reliability scores
  - Create SupplierReliabilityScore records for demo suppliers
  - Use realistic on-time delivery rates (0.7-0.95)
  - Use realistic quality acceptance rates (0.8-0.98)
  - Set calculation period to 90 days

- [ ] 17.4 Create demo scenario script
  - Create script to trigger demo pipeline execution
  - Reduce stock below reorder point for demo part
  - Wait for approval request to be created
  - Document demo flow for user acceptance testing

- [ ] 17.5 Configure Ollama with llama3 model
  - Pull llama3 model: `ollama pull llama3`
  - Verify Ollama is accessible from Django container
  - Test LLM decision-making with demo data

- [ ] 17.6 Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 18. Final Integration and Wiring
  - Wire all components together
  - Test complete system end-to-end
  - Verify all requirements met
  - _Requirements: All requirements_

- [ ] 18.1 Wire signal handlers to Django app
  - Register all signal handlers in apps.py ready() method
  - Verify signals trigger pipeline execution
  - Test with real StockItem.save() operations

- [ ] 18.2 Wire LangGraph nodes together
  - Connect all agent nodes in correct sequence
  - Add conditional edges for error handling
  - Add interrupt_before on human_approval node
  - Test graph execution with mock data

- [ ] 18.3 Wire notification service to approval gate
  - Connect ApprovalGate to NotificationService
  - Test in-app notification creation
  - Test email notification delivery
  - Verify notification content is correct


- [ ] 18.4 Wire learning layer to pipeline completion
  - Connect LearningLayer to execution node
  - Verify outcome logging after PO creation
  - Verify async tasks scheduled for retraining
  - Test reorder point adjustment

- [ ] 18.5 Wire API endpoints to frontend UI
  - Connect ApprovalActionView to approval buttons in UI
  - Connect PipelineStatusView to status indicators
  - Test API calls from frontend
  - Verify error handling in UI

- [ ] 18.6 Perform end-to-end system test
  - Trigger pipeline via stock change
  - Verify all agents execute correctly
  - Approve via UI
  - Verify PO created
  - Verify learning layer updated
  - Check all logs and metrics

- [ ] 18.7 Verify all requirements met
  - Review requirements document
  - Verify each requirement has corresponding implementation
  - Test each acceptance criterion
  - Document any deviations or limitations

- [ ] 18.8 Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at logical breaks
- Property tests validate universal correctness properties from design document
- Unit tests validate specific examples and edge cases
- Implementation follows the 6-phase roadmap from design document
- All code extends existing `ai_procurement/` without breaking current functionality
- Configuration is externalized via environment variables and config.py
- Security is built-in with permission checks, prompt sanitization, and audit logging
- Performance is optimized with caching, indexes, and async processing
- Error handling includes graceful degradation and clear user notifications

## Implementation Phases Summary

**Phase 1 (Weeks 1-2):** Tasks 1-2 - Foundation with database models, state management, and event triggering

**Phase 2 (Weeks 3-4):** Tasks 3-5 - Core agents (Demand, Supplier, Decision) with LLM integration

**Phase 3 (Week 5):** Tasks 6-7 - HITL approval gate and PO execution

**Phase 4 (Week 6):** Task 8 - Learning layer with continuous improvement

**Phase 5 (Week 7):** Tasks 9-15 - Integration, API, UI, security, performance, testing

**Phase 6 (Week 8):** Tasks 16-18 - Documentation, data seeding, final wiring, demo preparation


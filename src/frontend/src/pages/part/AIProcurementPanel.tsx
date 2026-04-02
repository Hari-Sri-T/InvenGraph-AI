import { useState, useEffect } from 'react';
import {
    Button,
    Card,
    Text,
    Group,
    Stack,
    Badge,
    Alert,
    Table,
    NumberInput,
    Select,
    Textarea,
    Divider,
    Progress,
    Timeline,
    Accordion,
} from '@mantine/core';
import {
    IconCheck,
    IconX,
    IconEdit,
    IconClock,
    IconTrendingUp,
    IconTrendingDown,
    IconMinus,
} from '@tabler/icons-react';

interface ApprovalRequest {
    request_id: string;
    pipeline_id: string;
    part_id: number;
    part_name: string;
    status: string;
    decision: {
        decision: string;
        recommended_quantity: number;
        recommended_supplier_id: number | null;
        reasoning: string;
        confidence_level: string;
        risk_factors: string[];
    };
    forecast: {
        predicted_demand: number;
        confidence_lower: number;
        confidence_upper: number;
        model_used: string;
        seasonality_detected: boolean;
        trend_direction: string;
    };
    suppliers: Array<{
        supplier_id: number;
        supplier_name: string;
        overall_score: number;
        price_score: number;
        lead_time_score: number;
        reliability_score: number;
        unit_price: number;
        estimated_delivery_days: number;
        ranking_position: number;
        recommendation_reason: string;
    }>;
    created_at: string;
    expires_at: string;
}

interface PipelineStatus {
    pipeline_id: string;
    part_id: number;
    status: string;
    current_node: string;
    trigger_reason: string;
    created_at: string;
    updated_at: string;
    completed_at: string | null;
    error_message: string | null;
}

export default function AIProcurementPanel({ partId }: { partId: any }) {
    const [loading, setLoading] = useState(false);
    const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
    const [pipelines, setPipelines] = useState<PipelineStatus[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [modifyMode, setModifyMode] = useState<string | null>(null);
    const [modifiedQuantity, setModifiedQuantity] = useState<number>(0);
    const [modifiedSupplier, setModifiedSupplier] = useState<string | null>(null);
    const [userNotes, setUserNotes] = useState<string>('');

    // Helper to grab Django's CSRF token from cookies
    const getCsrfToken = () => {
        return (
            document.cookie
                .split('; ')
                .find((row) => row.startsWith('csrftoken='))
                ?.split('=')[1] || ''
        );
    };

    // Fetch pending approvals
    const fetchApprovals = async () => {
        try {
            const res = await fetch(
                `/api/ai/procurement/approvals/?part_id=${partId}&status=pending`,
                {
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                    },
                }
            );
            const json = await res.json();
            if (res.ok) {
                setApprovals(json.approvals || []);
            }
        } catch (err: any) {
            console.error('Failed to fetch approvals:', err);
        }
    };

    // Fetch pipeline status
    const fetchPipelines = async () => {
        try {
            const res = await fetch(`/api/ai/procurement/pipeline/status/?part_id=${partId}`, {
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                },
            });
            const json = await res.json();
            if (res.ok) {
                setPipelines(json.pipelines || []);
            }
        } catch (err: any) {
            console.error('Failed to fetch pipelines:', err);
        }
    };

    // Auto-refresh approvals and pipelines
    useEffect(() => {
        fetchApprovals();
        fetchPipelines();
        const interval = setInterval(() => {
            fetchApprovals();
            fetchPipelines();
        }, 10000); // Refresh every 10 seconds
        return () => clearInterval(interval);
    }, [partId]);

    // Trigger new pipeline
    const triggerPipeline = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch('/api/ai/procurement/pipeline/trigger/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ part_id: partId }),
            });
            const json = await res.json();
            if (!res.ok) throw new Error(json.error || 'Failed to trigger pipeline');

            // Refresh data
            await fetchPipelines();
            await fetchApprovals();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    // Handle approval action
    const handleApprovalAction = async (
        requestId: string,
        action: 'approve' | 'reject' | 'modify'
    ) => {
        try {
            const body: any = { action, user_notes: userNotes };

            if (action === 'modify') {
                if (modifiedQuantity > 0) {
                    body.modified_quantity = modifiedQuantity;
                }
                if (modifiedSupplier) {
                    body.modified_supplier_id = parseInt(modifiedSupplier);
                }
            }

            const res = await fetch(`/api/ai/procurement/approvals/${requestId}/action/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify(body),
            });

            const json = await res.json();
            if (!res.ok) throw new Error(json.error || 'Failed to process approval');

            // Reset state
            setModifyMode(null);
            setModifiedQuantity(0);
            setModifiedSupplier(null);
            setUserNotes('');

            // Refresh data
            await fetchApprovals();
            await fetchPipelines();

            alert(`Success! ${json.message}`);
        } catch (err: any) {
            alert(`Error: ${err.message}`);
        }
    };

    // Get status badge color
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'running':
                return 'blue';
            case 'interrupted':
                return 'yellow';
            case 'completed':
                return 'green';
            case 'failed':
                return 'red';
            case 'rejected':
                return 'gray';
            default:
                return 'gray';
        }
    };

    // Get trend icon
    const getTrendIcon = (trend: string) => {
        switch (trend) {
            case 'increasing':
                return <IconTrendingUp size={16} />;
            case 'decreasing':
                return <IconTrendingDown size={16} />;
            default:
                return <IconMinus size={16} />;
        }
    };

    return (
        <Card withBorder shadow="sm" radius="md" p="md" mt="md">
            <Stack gap="md">
                <Group justify="space-between">
                    <Text fw={700} size="lg">
                        🤖 Agentic AI Procurement
                    </Text>
                    <Button onClick={triggerPipeline} loading={loading} color="blue">
                        Trigger Pipeline
                    </Button>
                </Group>

                {error && <Alert color="red">{error}</Alert>}

                {/* Pipeline Status */}
                {pipelines.length > 0 && (
                    <Accordion variant="contained">
                        <Accordion.Item value="pipelines">
                            <Accordion.Control>
                                <Group>
                                    <Text fw={600}>Recent Pipelines</Text>
                                    <Badge>{pipelines.length}</Badge>
                                </Group>
                            </Accordion.Control>
                            <Accordion.Panel>
                                <Timeline active={-1} bulletSize={24} lineWidth={2}>
                                    {pipelines.slice(0, 5).map((pipeline) => (
                                        <Timeline.Item
                                            key={pipeline.pipeline_id}
                                            bullet={
                                                pipeline.status === 'completed' ? (
                                                    <IconCheck size={12} />
                                                ) : pipeline.status === 'failed' ? (
                                                    <IconX size={12} />
                                                ) : (
                                                    <IconClock size={12} />
                                                )
                                            }
                                            title={
                                                <Group gap="xs">
                                                    <Badge
                                                        size="sm"
                                                        color={getStatusColor(pipeline.status)}
                                                    >
                                                        {pipeline.status}
                                                    </Badge>
                                                    <Text size="sm">{pipeline.current_node}</Text>
                                                </Group>
                                            }
                                        >
                                            <Text size="xs" c="dimmed">
                                                {pipeline.trigger_reason}
                                            </Text>
                                            <Text size="xs" c="dimmed">
                                                {new Date(pipeline.created_at).toLocaleString()}
                                            </Text>
                                        </Timeline.Item>
                                    ))}
                                </Timeline>
                            </Accordion.Panel>
                        </Accordion.Item>
                    </Accordion>
                )}

                {/* Pending Approvals */}
                {approvals.length > 0 && (
                    <Stack gap="md">
                        <Divider label="Pending Approvals" labelPosition="center" />

                        {approvals.map((approval) => (
                            <Card
                                key={approval.request_id}
                                withBorder
                                shadow="sm"
                                p="md"
                                style={{ backgroundColor: '#f8f9fa' }}
                            >
                                <Stack gap="sm">
                                    {/* Header */}
                                    <Group justify="space-between">
                                        <Text fw={600} size="lg">
                                            Approval Required
                                        </Text>
                                        <Badge
                                            size="lg"
                                            color={
                                                approval.decision.confidence_level === 'high'
                                                    ? 'green'
                                                    : approval.decision.confidence_level === 'low'
                                                      ? 'red'
                                                      : 'yellow'
                                            }
                                        >
                                            {approval.decision.confidence_level} confidence
                                        </Badge>
                                    </Group>

                                    {/* Forecast Summary */}
                                    <Card withBorder p="sm">
                                        <Text fw={600} size="sm" mb="xs">
                                            📊 Demand Forecast (30 days)
                                        </Text>
                                        <Group gap="md">
                                            <Badge color="grape" size="lg">
                                                {approval.forecast.predicted_demand?.toFixed(0) ||
                                                    'N/A'}{' '}
                                                units
                                            </Badge>
                                            <Badge color="gray" variant="light">
                                                {approval.forecast.model_used}
                                            </Badge>
                                            <Group gap={4}>
                                                {getTrendIcon(approval.forecast.trend_direction)}
                                                <Text size="sm">
                                                    {approval.forecast.trend_direction}
                                                </Text>
                                            </Group>
                                        </Group>
                                        {approval.forecast.confidence_lower !== undefined && (
                                            <Text size="xs" c="dimmed" mt="xs">
                                                Range: {approval.forecast.confidence_lower.toFixed(0)}{' '}
                                                - {approval.forecast.confidence_upper.toFixed(0)}{' '}
                                                units
                                            </Text>
                                        )}
                                    </Card>

                                    {/* AI Decision */}
                                    <Card withBorder p="sm">
                                        <Text fw={600} size="sm" mb="xs">
                                            🤖 AI Recommendation
                                        </Text>
                                        <Group gap="md" mb="xs">
                                            <Badge
                                                size="lg"
                                                color={
                                                    approval.decision.decision === 'ORDER'
                                                        ? 'green'
                                                        : 'gray'
                                                }
                                            >
                                                {approval.decision.decision}
                                            </Badge>
                                            <Text fw={600}>
                                                {approval.decision.recommended_quantity} units
                                            </Text>
                                        </Group>
                                        <Text size="sm">{approval.decision.reasoning}</Text>
                                        {approval.decision.risk_factors.length > 0 && (
                                            <Alert color="yellow" mt="xs" p="xs">
                                                <Text size="xs" fw={600}>
                                                    Risk Factors:
                                                </Text>
                                                <ul style={{ margin: 0, paddingLeft: 20 }}>
                                                    {approval.decision.risk_factors.map(
                                                        (risk, idx) => (
                                                            <li key={idx}>
                                                                <Text size="xs">{risk}</Text>
                                                            </li>
                                                        )
                                                    )}
                                                </ul>
                                            </Alert>
                                        )}
                                    </Card>

                                    {/* Supplier Comparison */}
                                    {approval.suppliers.length > 0 && (
                                        <Card withBorder p="sm">
                                            <Text fw={600} size="sm" mb="xs">
                                                🏭 Top Suppliers
                                            </Text>
                                            <Table striped highlightOnHover>
                                                <Table.Thead>
                                                    <Table.Tr>
                                                        <Table.Th>Rank</Table.Th>
                                                        <Table.Th>Supplier</Table.Th>
                                                        <Table.Th>Score</Table.Th>
                                                        <Table.Th>Price</Table.Th>
                                                        <Table.Th>Lead Time</Table.Th>
                                                    </Table.Tr>
                                                </Table.Thead>
                                                <Table.Tbody>
                                                    {approval.suppliers.map((supplier) => (
                                                        <Table.Tr
                                                            key={supplier.supplier_id}
                                                            style={{
                                                                backgroundColor:
                                                                    supplier.supplier_id ===
                                                                    approval.decision
                                                                        .recommended_supplier_id
                                                                        ? '#e7f5ff'
                                                                        : undefined,
                                                            }}
                                                        >
                                                            <Table.Td>
                                                                <Badge size="sm">
                                                                    #{supplier.ranking_position}
                                                                </Badge>
                                                            </Table.Td>
                                                            <Table.Td>
                                                                <Text size="sm" fw={600}>
                                                                    {supplier.supplier_name}
                                                                </Text>
                                                                <Text size="xs" c="dimmed">
                                                                    {supplier.recommendation_reason}
                                                                </Text>
                                                            </Table.Td>
                                                            <Table.Td>
                                                                <Progress
                                                                    value={
                                                                        supplier.overall_score * 100
                                                                    }
                                                                    size="sm"
                                                                    color="blue"
                                                                />
                                                                <Text size="xs">
                                                                    {(
                                                                        supplier.overall_score * 100
                                                                    ).toFixed(0)}
                                                                    %
                                                                </Text>
                                                            </Table.Td>
                                                            <Table.Td>
                                                                ${supplier.unit_price.toFixed(2)}
                                                            </Table.Td>
                                                            <Table.Td>
                                                                {supplier.estimated_delivery_days}{' '}
                                                                days
                                                            </Table.Td>
                                                        </Table.Tr>
                                                    ))}
                                                </Table.Tbody>
                                            </Table>
                                        </Card>
                                    )}

                                    {/* Modify Mode */}
                                    {modifyMode === approval.request_id && (
                                        <Card withBorder p="sm" style={{ backgroundColor: '#fff' }}>
                                            <Text fw={600} size="sm" mb="xs">
                                                ✏️ Modify Order
                                            </Text>
                                            <Stack gap="sm">
                                                <NumberInput
                                                    label="Quantity"
                                                    placeholder={approval.decision.recommended_quantity.toString()}
                                                    value={modifiedQuantity}
                                                    onChange={(val) =>
                                                        setModifiedQuantity(Number(val))
                                                    }
                                                    min={0}
                                                />
                                                <Select
                                                    label="Supplier"
                                                    placeholder="Select supplier"
                                                    value={modifiedSupplier}
                                                    onChange={setModifiedSupplier}
                                                    data={approval.suppliers.map((s) => ({
                                                        value: s.supplier_id.toString(),
                                                        label: s.supplier_name,
                                                    }))}
                                                />
                                                <Textarea
                                                    label="Notes (optional)"
                                                    placeholder="Add any notes..."
                                                    value={userNotes}
                                                    onChange={(e) =>
                                                        setUserNotes(e.currentTarget.value)
                                                    }
                                                    rows={2}
                                                />
                                            </Stack>
                                        </Card>
                                    )}

                                    {/* Action Buttons */}
                                    <Group justify="flex-end" gap="sm">
                                        {modifyMode === approval.request_id ? (
                                            <>
                                                <Button
                                                    variant="subtle"
                                                    onClick={() => setModifyMode(null)}
                                                >
                                                    Cancel
                                                </Button>
                                                <Button
                                                    color="blue"
                                                    leftSection={<IconCheck size={16} />}
                                                    onClick={() =>
                                                        handleApprovalAction(
                                                            approval.request_id,
                                                            'modify'
                                                        )
                                                    }
                                                >
                                                    Confirm Changes
                                                </Button>
                                            </>
                                        ) : (
                                            <>
                                                <Button
                                                    variant="subtle"
                                                    color="red"
                                                    leftSection={<IconX size={16} />}
                                                    onClick={() =>
                                                        handleApprovalAction(
                                                            approval.request_id,
                                                            'reject'
                                                        )
                                                    }
                                                >
                                                    Reject
                                                </Button>
                                                <Button
                                                    variant="light"
                                                    color="blue"
                                                    leftSection={<IconEdit size={16} />}
                                                    onClick={() => {
                                                        setModifyMode(approval.request_id);
                                                        setModifiedQuantity(
                                                            approval.decision.recommended_quantity
                                                        );
                                                        setModifiedSupplier(
                                                            approval.decision.recommended_supplier_id?.toString() ||
                                                                null
                                                        );
                                                    }}
                                                >
                                                    Modify
                                                </Button>
                                                <Button
                                                    color="green"
                                                    leftSection={<IconCheck size={16} />}
                                                    onClick={() =>
                                                        handleApprovalAction(
                                                            approval.request_id,
                                                            'approve'
                                                        )
                                                    }
                                                >
                                                    Approve
                                                </Button>
                                            </>
                                        )}
                                    </Group>

                                    {/* Expiration */}
                                    <Text size="xs" c="dimmed" ta="right">
                                        Expires: {new Date(approval.expires_at).toLocaleString()}
                                    </Text>
                                </Stack>
                            </Card>
                        ))}
                    </Stack>
                )}

                {/* No approvals message */}
                {approvals.length === 0 && pipelines.length === 0 && (
                    <Alert color="blue" title="No Active Pipelines">
                        Click "Trigger Pipeline" to start an AI procurement analysis for this part.
                    </Alert>
                )}

                {approvals.length === 0 && pipelines.length > 0 && (
                    <Alert color="gray" title="No Pending Approvals">
                        All pipelines have been processed. Trigger a new pipeline to generate
                        recommendations.
                    </Alert>
                )}
            </Stack>
        </Card>
    );
}
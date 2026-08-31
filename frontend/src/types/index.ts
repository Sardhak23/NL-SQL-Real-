/**
 * NL-SQL Analytics Copilot - TypeScript Data Contracts & Models
 */

export type Dialect = 'sqlite' | 'postgres' | 'mysql' | 'snowflake';

export interface ColumnMetadata {
  name: string;
  type: string;
  is_pk: boolean;
  is_fk: boolean;
  nullable?: boolean;
}

export interface ForeignKeyMetadata {
  column: string;
  referenced_table: string;
  referenced_column: string;
}

export interface TableMetadata {
  name: string;
  row_count: number;
  description?: string;
  columns: ColumnMetadata[];
  foreign_keys?: ForeignKeyMetadata[];
}

export interface SchemaResponse {
  database_name: string;
  dialect: string;
  total_tables: number;
  total_rows: number;
  tables: TableMetadata[];
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'error';
  version: string;
  database_connected: boolean;
  database_file: string;
  total_orders?: number;
  llm_provider: string;
  llm_available: boolean;
  offline_mode_ready: boolean;
  timestamp: string;
}

export interface MetricItem {
  label: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down' | 'neutral';
}

export interface ExecutiveSummary {
  headline: string;
  key_metrics: MetricItem[];
  bullet_points: string[];
  actionable_recommendations?: string[];
}

export type ChartType =
  | 'bar'
  | 'horizontal_bar'
  | 'line'
  | 'area'
  | 'pie'
  | 'donut'
  | 'scatter'
  | 'metric'
  | 'table'
  | 'none';

export interface ChartSpec {
  chart_type: ChartType;
  title: string;
  description?: string;
  x_axis?: string;
  y_axis?: string;
  secondary_y_axis?: string;
  is_plottable?: boolean;
  format?: 'currency' | 'number' | 'percentage' | 'string';
}

export interface PipelineTimings {
  schema_linking_ms?: number;
  sql_generation_ms?: number;
  ast_validation_ms?: number;
  db_execution_ms?: number;
  insight_synthesis_ms?: number;
  total_latency_ms?: number;
}

export interface QueryRequest {
  question: string;
  conversation_id?: string;
  dialect?: Dialect;
  temperature?: number;
  max_retries?: number;
  offline_mode?: boolean;
}

export interface QueryResponse {
  success: boolean;
  question: string;
  sql: string;
  columns: string[];
  rows: Record<string, any>[];
  row_count: number;
  execution_time_ms: number;
  correction_attempts: number;
  correction_log?: Array<{
    attempt: number;
    error: string;
    attempted_sql: string;
    correction: string;
  }>;
  explanation: string;
  sql_breakdown?: {
    select?: string;
    from?: string;
    join?: string[];
    where?: string;
    group_by?: string;
    order_by?: string;
    limit?: string;
  };
  executive_summary: ExecutiveSummary;
  chart_spec: ChartSpec;
  suggested_followups: string[];
  pipeline_timings?: PipelineTimings;
  error?: string | null;
}

export type StepStatus = 'pending' | 'running' | 'completed' | 'error' | 'skipped';

export interface ExecutionStep {
  id: string;
  name: string;
  description: string;
  status: StepStatus;
  durationMs?: number;
  details?: string;
}

export interface HistoryItem {
  id: string;
  question: string;
  timestamp: string;
  rowCount: number;
  executionTimeMs: number;
  response: QueryResponse;
}

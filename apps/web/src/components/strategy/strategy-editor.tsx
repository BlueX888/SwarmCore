import type { Diagnostic, SavedConfiguration } from "@/api/types";
import { StrategyCanvas } from "./strategy-canvas";
import type { EditorState, SwarmSpecDocument } from "./strategy-editor-model";

export function StrategyEditor({
  spec,
  editorState,
  nodeTypes,
  models = [],
  tools = [],
  agentConfigurations = [],
  agentConfigurationsLoading = false,
  agentConfigurationsError,
  diagnostics,
  onSpecChange,
  onEditorStateChange,
  onError,
}: {
  spec: SwarmSpecDocument;
  editorState: EditorState;
  nodeTypes: string[];
  models?: string[];
  tools?: string[];
  agentConfigurations?: SavedConfiguration[];
  agentConfigurationsLoading?: boolean;
  agentConfigurationsError?: string;
  diagnostics: Diagnostic[];
  onSpecChange: (spec: SwarmSpecDocument) => void;
  onEditorStateChange: (state: EditorState) => void;
  onError: (message: string) => void;
}) {
  return <div className="min-w-0 space-y-4">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <p className="text-sm font-medium text-gray-700 dark:text-gray-300">策略编辑器</p>
        <p className="text-xs text-gray-500">SwarmSpec 是执行来源，画布布局会单独保存。</p>
      </div>
    </div>
    <StrategyCanvas
      spec={spec}
      editorState={editorState}
      nodeTypes={nodeTypes}
      models={models}
      tools={tools}
      agentConfigurations={agentConfigurations}
      agentConfigurationsLoading={agentConfigurationsLoading}
      agentConfigurationsError={agentConfigurationsError}
      diagnostics={diagnostics}
      onSpecChange={onSpecChange}
      onEditorStateChange={onEditorStateChange}
      onError={onError}
    />
  </div>;
}

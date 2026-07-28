import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { describe, expect, it, vi } from "vitest";
import type { ApprovalRequest } from "@/api/types";
import { HumanApprovalCard, resolveApprovalGuide } from "@/components/operations/human-action-card";

const publishReview: ApprovalRequest = {
  approvalId: "approval-1",
  runId: "019fa704-bd47-7def-970f-a92796a1a20c",
  nodeKey: "publish-review",
  prompt: "请核对合同履约候选计划、证据定位、冲突和甘特基准后发布。",
  inputSchema: {
    type: "object",
    required: ["approved"],
    properties: {
      approved: { type: "boolean" },
      confirmations: { type: "array" },
      comment: { type: "string" },
    },
  },
  status: "PENDING",
  allowedActions: ["approve", "reject"],
  requestedBy: "system",
  handledBy: null,
  createdAt: "2026-07-28T00:00:00Z",
  handledAt: null,
};

describe("resolveApprovalGuide", () => {
  it("maps publish-review to a Chinese publish checklist", () => {
    const guide = resolveApprovalGuide("publish-review", publishReview.prompt);
    expect(guide.title).toContain("发布审批");
    expect(guide.checklist).toEqual(expect.arrayContaining(["候选履约计划", "甘特基准时间线"]));
    expect(guide.approveLabel).toBe("批准并发布");
  });
});

describe("HumanApprovalCard", () => {
  it("explains what to do and submits approved=true without showing English field keys", () => {
    const onApprove = vi.fn();
    const onReject = vi.fn();
    window.confirm = vi.fn();

    render(
      <MemoryRouter>
        <HumanApprovalCard
          request={publishReview}
          runPath="/runs/019fa704-bd47-7def-970f-a92796a1a20c"
          busy={false}
          onApprove={onApprove}
          onReject={onReject}
        />
      </MemoryRouter>,
    );

    expect(screen.getByText("合同履约计划 · 发布审批")).toBeVisible();
    expect(screen.getByText("你需要做什么")).toBeVisible();
    expect(screen.getByText("打开运行详情核对")).toBeVisible();
    expect(screen.queryByText("approved")).not.toBeInTheDocument();
    expect(screen.getByText("审批意见")).toBeVisible();
    expect(screen.getByText("核对说明")).toBeVisible();

    fireEvent.change(screen.getByPlaceholderText("例如：已核对材料，同意继续。"), {
      target: { value: "已核对，可发布" },
    });
    fireEvent.change(screen.getByPlaceholderText("每行一条核对说明"), {
      target: { value: "已核对候选计划\n已核对甘特基准" },
    });
    fireEvent.click(screen.getByRole("button", { name: "批准并发布" }));

    expect(onApprove).toHaveBeenCalledWith({
      approved: true,
      comment: "已核对，可发布",
      confirmations: ["已核对候选计划", "已核对甘特基准"],
    });
  });
});

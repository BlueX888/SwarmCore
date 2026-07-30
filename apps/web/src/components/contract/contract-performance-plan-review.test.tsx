import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { TaskSnapshot } from "@/api/types";
import {
  ContractPerformancePlanReviewView,
  contractPerformancePlanReviewFromTasks,
} from "./contract-performance-plan-review";

function task(nodeKey: string, content: Record<string, unknown>): TaskSnapshot {
  return {
    taskId: `task-${nodeKey}`,
    nodeKey,
    nodeType: "tool",
    status: "SUCCEEDED",
    dependencies: [],
    output: { content },
    retryGeneration: 0,
    allowedActions: [],
  };
}

const plan = {
  schemaVersion: "schema://contract-performance/plan@1",
  status: "REVIEW_REQUIRED",
  contract: {
    contractNumber: "SC-REAL-2026-0728",
    currency: "CNY",
    totalAmount: 1_280_000,
  },
  milestones: [
    {
      id: "M3",
      name: "系统上线",
      dueDate: "2026-08-20",
      dependencies: ["M2"],
      evidenceRefs: [
        {
          documentVersionId: "document-version-1",
          page: 8,
          excerpt: "系统应在 2026 年 8 月 20 日前上线。",
        },
      ],
    },
  ],
  paymentConditions: [
    { id: "P1", name: "预付款", amount: 240_000 },
    { id: "P2", name: "到货款", amount: 360_000 },
    { id: "P3", name: "验收款", amount: 480_000 },
    { id: "P4", name: "质保金", amount: 120_000 },
  ],
  conflicts: [],
  gaps: [
    {
      code: "PAYMENT_TOTAL_MISMATCH",
      contractTotal: 1_280_000,
      paymentTotal: 1_200_000,
      difference: 80_000,
    },
  ],
};

describe("ContractPerformancePlanReviewView", () => {
  it("reads the interim plan from durable task output", () => {
    const review = contractPerformancePlanReviewFromTasks([
      task("apply-changes", {
        currentBaseline: plan,
        originalBaseline: {
          ...plan,
          contract: { ...plan.contract, totalAmount: 1_200_000 },
          milestones: [{ ...plan.milestones[0], dueDate: "2026-08-15" }],
          gaps: [],
        },
        differences: [
          {
            path: "/contract/totalAmount",
            before: 1_200_000,
            after: 1_280_000,
          },
        ],
        unapprovedChangeRisks: [],
      }),
      task("build-schedule", { quality: { status: "MILESTONE_ONLY" } }),
    ]);

    expect(review?.plan).toEqual(plan);
    expect(review?.differences).toHaveLength(1);
    expect(contractPerformancePlanReviewFromTasks([task("apply-changes", {})])).toBeNull();
  });

  it("shows totals, evidence location, approved changes, and review gaps", () => {
    const review = contractPerformancePlanReviewFromTasks([
      task("apply-changes", {
        currentBaseline: plan,
        originalBaseline: {
          ...plan,
          contract: { ...plan.contract, totalAmount: 1_200_000 },
          milestones: [{ ...plan.milestones[0], dueDate: "2026-08-15" }],
        },
        differences: [
          {
            path: "/contract/totalAmount",
            before: 1_200_000,
            after: 1_280_000,
          },
        ],
        unapprovedChangeRisks: [],
      }),
      task("build-schedule", { quality: { status: "MILESTONE_ONLY" } }),
    ]);
    if (!review) throw new Error("expected a contract plan review");

    render(<ContractPerformancePlanReviewView review={review} />);

    expect(screen.getByText("发布前候选履约计划")).toBeInTheDocument();
    expect(screen.getByText("CNY 1,280,000")).toBeInTheDocument();
    expect(screen.getByText("CNY 1,200,000")).toBeInTheDocument();
    expect(screen.getByText("PAYMENT_TOTAL_MISMATCH")).toBeInTheDocument();
    expect(screen.getByText(/document-version-1 · 第 8 页/)).toBeInTheDocument();
    expect(screen.getByText("截止 2026-08-20（原 2026-08-15） · 依赖 M2")).toBeInTheDocument();
    expect(screen.getByText("/contract/totalAmount")).toBeInTheDocument();
    expect(screen.getByText("MILESTONE_ONLY")).toBeInTheDocument();
  });

  it("derives payment amounts from rates and summarizes already-applied changes", () => {
    const ratePlan = {
      ...plan,
      status: "CANDIDATE",
      gaps: [],
      paymentConditions: [
        { id: "P1", title: "预付款", amount: null, rate: 0.2 },
        { id: "P2", title: "验收款", amount: null, rate: 0.8 },
      ],
      changes: [
        {
          id: "CR-001",
          title: "新增 ERP 库存接口",
          status: "APPROVED",
          effectiveAt: "2026-07-18",
        },
      ],
    };
    const review = contractPerformancePlanReviewFromTasks([
      task("apply-changes", {
        currentBaseline: ratePlan,
        originalBaseline: ratePlan,
        differences: [
          {
            path: "/contract/totalAmount",
            before: 1_280_000,
            after: 1_280_000,
          },
        ],
      }),
      task("build-schedule", { quality: { status: "MILESTONE_ONLY" } }),
    ]);
    if (!review) throw new Error("expected a contract plan review");

    render(<ContractPerformancePlanReviewView review={review} />);

    expect(screen.getByText("CNY 256,000 · 20%")).toBeInTheDocument();
    expect(screen.getByText("CNY 1,024,000 · 80%")).toBeInTheDocument();
    expect(screen.getByText("新增 ERP 库存接口")).toBeInTheDocument();
    expect(screen.getByText("已包含在候选基准 · 生效日 2026-07-18")).toBeInTheDocument();
  });
});

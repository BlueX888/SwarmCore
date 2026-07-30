import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import {
  asDocumentStructuring,
  DOCUMENT_STRUCTURING_SCHEMA,
  DocumentStructuringResultView,
} from "./document-structuring-result";

const result = {
  schemaVersion: DOCUMENT_STRUCTURING_SCHEMA as typeof DOCUMENT_STRUCTURING_SCHEMA,
  status: "READY",
  summary: "这是一个待填写业务信息的框架合同模板。",
  reviewRequired: false,
  qualityFlags: ["DOCUMENT_IS_TEMPLATE", "PLACEHOLDER_VALUES_NORMALIZED"],
  contentHash: "a".repeat(64),
  documents: [{
    documentId: "doc-1",
    documentVersionId: "version-1",
    filename: "dos-4-call-off-contract.odt",
    mediaType: "application/vnd.oasis.opendocument.text",
    sections: Array.from({ length: 67 }),
    chunks: Array.from({ length: 10 }),
    tables: Array.from({ length: 10 }),
    fields: [{
      fieldPath: "document.title",
      effectiveValue: "Digital Outcomes and Specialists 4 Framework Agreement Call-Off Contract",
    }],
    classification: {
      businessType: "CONTRACT",
      contractType: "CALL_OFF_CONTRACT",
      frameworkReference: "RM1043.6",
      governingLaw: "English Law",
    },
    organization: {
      buyer: { name: null },
      supplier: { name: null },
    },
  }],
  artifacts: [
    { artifactId: "artifact-1", filename: "structured-document.json" },
    { artifactId: "artifact-2", filename: "content.md" },
  ],
  humanReview: {
    decision: "CONFIRM",
    correctionCount: 0,
    reason: "已核对公开合同原文与结构化结果。",
  },
};

describe("document structuring result", () => {
  afterEach(cleanup);

  it("recognizes only the document structuring package schema", () => {
    expect(asDocumentStructuring(result)).not.toBeNull();
    expect(asDocumentStructuring({ ...result, schemaVersion: "other" })).toBeNull();
  });

  it("renders a business-readable result instead of the raw package", () => {
    render(<DocumentStructuringResultView result={result} />);

    expect(screen.getByRole("heading", { name: "文档结构化结论" })).toBeVisible();
    expect(screen.getByText("这是一个待填写业务信息的框架合同模板。")).toBeVisible();
    expect(screen.getByText("67")).toBeVisible();
    expect(screen.getByText("RM1043.6")).toBeVisible();
    expect(screen.getByText("模板待填写 / 模板待填写")).toBeVisible();
    expect(screen.getByText("structured-document.json")).toBeVisible();
    expect(screen.getByText("已核对公开合同原文与结构化结果。")).toBeVisible();
  });
});

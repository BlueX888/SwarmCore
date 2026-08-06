import { describe, expect, it } from "vitest";
import { DOCUMENT_CATEGORY_LABELS, documentBindingKeys } from "./business-works";

describe("documentBindingKeys", () => {
  it("lets report generation reuse contract post-evaluation documents", () => {
    expect(documentBindingKeys("report-generation", "contract-post-evaluation-case")).toEqual(
      expect.arrayContaining([
        "report-generation",
        "contract-post-evaluation",
        "contract-post-evaluation-case",
      ]),
    );
  });
});

describe("DOCUMENT_CATEGORY_LABELS", () => {
  it("maps procurement-supplier-risk categories to Chinese display names", () => {
    expect(DOCUMENT_CATEGORY_LABELS.TENDER_DOCUMENT).toBe("招标/采购文件");
    expect(DOCUMENT_CATEGORY_LABELS.WINNING_BID).toBe("中标投标/响应文件");
    expect(DOCUMENT_CATEGORY_LABELS.AWARD_NOTICE).toBe("中标/成交通知书");
    expect(DOCUMENT_CATEGORY_LABELS.MASTER_CONTRACT).toBe("待签或已签合同");
    expect(DOCUMENT_CATEGORY_LABELS.PROCUREMENT_CHANGE).toBe("澄清、变更和补充协议");
    expect(DOCUMENT_CATEGORY_LABELS.SUPPLIER_PERFORMANCE).toBe("供应商履约绩效资料");
  });
});

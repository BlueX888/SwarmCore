import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { afterEach, describe, expect, it } from "vitest";
import { LegacyCapabilityPackDetailRedirect, LegacyCapabilityPackListRedirect } from "@/components/legacy-capability-pack-redirect";

function renderAt(path: string) {
  return render(<MemoryRouter initialEntries={[path]}><Routes>
    <Route path="/capability-packs" element={<LegacyCapabilityPackListRedirect />} />
    <Route path="/capability-packs/:packName" element={<LegacyCapabilityPackDetailRedirect mode="settings" />} />
    <Route path="/capability-packs/:packName/workbench" element={<LegacyCapabilityPackDetailRedirect mode="workbench" />} />
    <Route path="/business-works" element={<h1>业务工作总览</h1>} />
    <Route path="/business-works/:workKey/settings" element={<h1>项目配置</h1>} />
    <Route path="/business-works/:workKey/workbench" element={<h1>业务工作台</h1>} />
  </Routes></MemoryRouter>);
}

describe("legacy capability pack redirects", () => {
  afterEach(cleanup);

  it("redirects the pack list to business works", async () => {
    renderAt("/capability-packs");
    expect(await screen.findByRole("heading", { name: "业务工作总览" })).toBeVisible();
  });

  it("maps known packs to business work settings and workbench", async () => {
    renderAt("/capability-packs/contract-integrity");
    expect(await screen.findByRole("heading", { name: "项目配置" })).toBeVisible();
    cleanup();
    renderAt("/capability-packs/contract-post-evaluation/workbench");
    expect(await screen.findByRole("heading", { name: "业务工作台" })).toBeVisible();
  });

  it("falls back to the catalog when a pack cannot be mapped", async () => {
    renderAt("/capability-packs/unknown-pack");
    expect(await screen.findByRole("heading", { name: "业务工作总览" })).toBeVisible();
  });
});

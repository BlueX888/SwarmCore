import { describe, expect, it } from "vitest";
import { filesystemToolInputError, isHostAbsolutePath } from "./filesystem-tool-config";

describe("filesystemToolInputError", () => {
  it("rejects host absolute paths for filesystem tools", () => {
    expect(isHostAbsolutePath("/etc/passwd")).toBe(true);
    expect(isHostAbsolutePath("C:\\Windows\\system32")).toBe(true);
    expect(isHostAbsolutePath("\\\\server\\share")).toBe(true);
    expect(isHostAbsolutePath("notes/hello.txt")).toBe(false);
    expect(
      filesystemToolInputError("tool://filesystem/read-text@1", {
        mount: "workspace",
        path: "/etc/passwd",
      }),
    ).toMatch(/相对路径/);
    expect(
      filesystemToolInputError("tool://filesystem/write-text@1", {
        mount: "workspace",
        path: "notes/a.txt",
        root: "C:/data",
      }),
    ).toMatch(/物理根目录/);
    expect(
      filesystemToolInputError("tool://search@1", {
        path: "/etc/passwd",
      }),
    ).toBeNull();
  });
});

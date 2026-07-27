const ABSOLUTE_PATH =
  /^(?:[a-zA-Z]:[\\/]|\\\\|\/\/|\/|\\)/;

export function isHostAbsolutePath(value: string): boolean {
  return ABSOLUTE_PATH.test(value.trim());
}

export function filesystemToolInputError(sourceRef: string, input: Record<string, unknown>): string | null {
  if (!sourceRef.startsWith("tool://filesystem/")) {
    return null;
  }
  const path = input.path;
  if (typeof path === "string" && isHostAbsolutePath(path)) {
    return "文件系统工具只能使用逻辑 mount 下的相对路径，不能填写宿主机绝对路径。";
  }
  if ("root" in input || "absolutePath" in input || "hostPath" in input) {
    return "文件系统工具不能配置物理根目录或宿主路径。";
  }
  return null;
}

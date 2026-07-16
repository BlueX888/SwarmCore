import * as React from "react";
import {
  SearchCommand,
  type SearchCommandGroup,
  type SearchCommandItem,
  type SearchCommandProps,
} from "@/components/ui/search-command";

export type SearchCommandStaticProps = Omit<SearchCommandProps, "onItemSelect"> & {
  /** 覆盖默认 navigate；无 react-router 时用于 href 跳转 */
  onItemSelect?: (item: SearchCommandItem) => void;
};

/**
 * @deprecated 无 react-router 环境使用。优先在 SearchCommand 上传 onItemSelect。
 * 兼容至 G50，见 references/migration-notes/MN-02-search-command-no-router.md
 */
export function SearchCommandStatic({
  onItemSelect,
  ...props
}: SearchCommandStaticProps) {
  const handleSelect = React.useCallback(
    (item: SearchCommandItem) => {
      if (onItemSelect) {
        onItemSelect(item);
        return;
      }
      if (item.href) {
        window.location.assign(item.href);
        return;
      }
      item.onSelect?.();
    },
    [onItemSelect],
  );

  return <SearchCommand {...props} onItemSelect={handleSelect} />;
}

export type { SearchCommandGroup, SearchCommandItem };

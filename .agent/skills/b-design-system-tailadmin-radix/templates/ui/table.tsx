import * as React from "react";
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

export type TableSize = "comfortable" | "compact" | "spacious";
export type TableVariant = "plain" | "bordered";

const tableWrapperVariants = cva(
  "relative w-full overflow-auto rounded-xl bg-white dark:bg-white/[0.03]",
  {
    variants: {
      variant: {
        plain: "border border-gray-200 dark:border-white/[0.05]",
        bordered: "border border-gray-300 dark:border-gray-700",
      },
      stickyHeader: {
        true: "",
        false: "",
      },
    },
    defaultVariants: { variant: "plain", stickyHeader: false },
  },
);

const tableHeadCellVariants = cva("", {
  variants: {
    size: {
      comfortable: "h-12 px-5",
      compact: "h-9 px-3",
      spacious: "h-14 px-6",
    },
    sticky: {
      true: "sticky top-0 z-10 bg-white dark:bg-gray-900",
      false: "",
    },
  },
  defaultVariants: { size: "comfortable", sticky: false },
});

const tableCellVariants = cva(
  "align-middle text-theme-sm text-gray-800 dark:text-white/90",
  {
    variants: {
      size: {
        comfortable: "px-5 py-4",
        compact: "px-3 py-2",
        spacious: "px-6 py-5",
      },
    },
    defaultVariants: { size: "comfortable" },
  },
);

type TableContextValue = {
  size: TableSize;
  variant: TableVariant;
  stickyHeader: boolean;
};

const TableContext = React.createContext<TableContextValue>({
  size: "comfortable",
  variant: "plain",
  stickyHeader: false,
});

export type TableProps = React.HTMLAttributes<HTMLTableElement> & {
  size?: TableSize;
  variant?: TableVariant;
  stickyHeader?: boolean;
  wrapperClassName?: string;
};

const Table = React.forwardRef<HTMLTableElement, TableProps>(
  (
    {
      className,
      size = "comfortable",
      variant = "plain",
      stickyHeader = false,
      wrapperClassName,
      ...props
    },
    ref,
  ) => (
    <TableContext.Provider value={{ size, variant, stickyHeader }}>
      <div
        className={cn(
          tableWrapperVariants({ variant, stickyHeader }),
          wrapperClassName,
        )}
      >
        <table
          ref={ref}
          data-size={size}
          data-variant={variant}
          className={cn("w-full caption-bottom text-sm", className)}
          {...props}
        />
      </div>
    </TableContext.Provider>
  ),
);
Table.displayName = "Table";

const TableHeader = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <thead ref={ref} className={cn("[&_tr]:border-b", className)} {...props} />
));
TableHeader.displayName = "TableHeader";

const TableBody = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <tbody
    ref={ref}
    className={cn("[&_tr:last-child]:border-0", className)}
    {...props}
  />
));
TableBody.displayName = "TableBody";

const TableFooter = React.forwardRef<
  HTMLTableSectionElement,
  React.HTMLAttributes<HTMLTableSectionElement>
>(({ className, ...props }, ref) => (
  <tfoot
    ref={ref}
    className={cn(
      "border-t border-gray-100 bg-gray-50 font-medium dark:border-white/[0.05] dark:bg-white/[0.02] [&>tr]:last:border-b-0",
      className,
    )}
    {...props}
  />
));
TableFooter.displayName = "TableFooter";

const TableRow = React.forwardRef<
  HTMLTableRowElement,
  React.HTMLAttributes<HTMLTableRowElement>
>(({ className, ...props }, ref) => (
  <tr
    ref={ref}
    className={cn(
      "border-b border-gray-100 transition-colors hover:bg-gray-50 data-[state=selected]:bg-brand-50 dark:border-white/[0.05] dark:hover:bg-white/[0.02] dark:data-[state=selected]:bg-brand-500/10",
      className,
    )}
    {...props}
  />
));
TableRow.displayName = "TableRow";

type TableHeadProps = React.ThHTMLAttributes<HTMLTableCellElement> & {
  size?: TableSize;
};

const TableHead = React.forwardRef<HTMLTableCellElement, TableHeadProps>(
  ({ className, size: sizeProp, ...props }, ref) => {
    const { size: contextSize, stickyHeader } = React.useContext(TableContext);
    const size = sizeProp ?? contextSize;

    return (
      <th
        ref={ref}
        className={cn(
          "text-left align-middle text-theme-xs font-medium text-gray-500 dark:text-gray-400 [&:has([role=checkbox])]:pr-0",
          tableHeadCellVariants({ size, sticky: stickyHeader }),
          className,
        )}
        {...props}
      />
    );
  },
);
TableHead.displayName = "TableHead";

type TableCellProps = React.TdHTMLAttributes<HTMLTableCellElement> & {
  size?: TableSize;
};

const TableCell = React.forwardRef<HTMLTableCellElement, TableCellProps>(
  ({ className, size: sizeProp, ...props }, ref) => {
    const { size: contextSize, variant } = React.useContext(TableContext);
    const size = sizeProp ?? contextSize;

    return (
      <td
        ref={ref}
        className={cn(
          tableCellVariants({ size }),
          variant === "bordered" &&
            "border-r border-gray-100 last:border-r-0 dark:border-white/[0.05]",
          "[&:has([role=checkbox])]:pr-0",
          className,
        )}
        {...props}
      />
    );
  },
);
TableCell.displayName = "TableCell";

const TableCaption = React.forwardRef<
  HTMLTableCaptionElement,
  React.HTMLAttributes<HTMLTableCaptionElement>
>(({ className, ...props }, ref) => (
  <caption
    ref={ref}
    className={cn("mt-4 text-theme-sm text-gray-500", className)}
    {...props}
  />
));
TableCaption.displayName = "TableCaption";

export {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableHead,
  TableRow,
  TableCell,
  TableCaption,
};

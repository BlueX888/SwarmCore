# Composite — Search / UserMenu / MultiSelect

## Header Search

**源**：`layout/AppHeader.tsx`

可复制模板：`templates/layout/app-header.tsx`（`HeaderSearch`）· `templates/ui/search-command.tsx`

```tsx
// wrapper: relative hidden xl:block
// input: h-11 w-full max-w-[430px] rounded-lg border-gray-200 bg-transparent pl-12 pr-14
// icon: absolute left-4 top-1/2 -translate-y-1/2
// shortcut badge: absolute right-2.5 rounded-lg border px-1.5 text-xs text-gray-400
```

快捷键：`Meta+k` / `Ctrl+k` 打开 `SearchCommand` 面板（`useSearchCommand`）。

## Command Palette / Combobox

**推荐**：`templates/ui/command.tsx` + `templates/ui/search-command.tsx`

```tsx
import { SearchCommand, useSearchCommand } from "@/components/ui/search-command";

const { open, setOpen } = useSearchCommand();

<SearchCommand
  open={open}
  onOpenChange={setOpen}
  groups={[
    {
      heading: "Pages",
      items: [
        { id: "dashboard", label: "Dashboard", href: "/", shortcut: "⌘D" },
        { id: "analytics", label: "Analytics", href: "/analytics" },
      ],
    },
    {
      heading: "Actions",
      items: [
        { id: "new-order", label: "Create order", onSelect: () => {} },
      ],
    },
  ]}
/>
```

Combobox（可搜索 Select / MultiSelect）：

```tsx
import { ComboboxPanel } from "@/components/ui/search-command";

<PopoverContent className="w-[280px] rounded-xl p-0 shadow-theme-lg">
  <ComboboxPanel options={options} value={value} onValueChange={setValue} />
</PopoverContent>
```

- 面板：`rounded-xl shadow-theme-lg`；选中项 `bg-brand-50 text-brand-500`
- 空态：`CommandEmpty` 居中文案
- 键盘：`CommandInput` 可过滤；`aria-selected` 高亮

## UserDropdown

**源**：`header/UserDropdown.tsx`

可复制模板：`templates/layout/user-dropdown.tsx`

```tsx
import { UserDropdown } from "@/components/layout/user-dropdown";

<UserDropdown
  name="Musharof"
  email="randomuser@pimjo.com"
  avatar="/images/user/owner.png"
  menuItems={[
    { id: "profile", label: "Edit profile", icon: <UserIcon />, href: "/profile" },
    { id: "settings", label: "Account settings", icon: <SettingsIcon />, href: "/settings" },
  ]}
  signOutHref="/signin"
/>
```

- Trigger：Avatar `size-11` + 名称 + ChevronDown（open 时 `rotate-180`）
- Panel：`rounded-2xl border shadow-theme-lg w-[260px]`
- 项：图标 + 文案 + `hover:bg-gray-100`
- 用 `DropdownMenu` + `DropdownMenuContent align="end"`

## NotificationDropdown

**源**：`header/NotificationDropdown.tsx`

可复制模板：`templates/layout/notification-dropdown.tsx`

```tsx
import { NotificationDropdown } from "@/components/layout/notification-dropdown";

<NotificationDropdown
  hasUnread
  items={[
    {
      id: "1",
      name: "Terry Franci",
      message: "requests permission to change",
      category: "Project",
      time: "5 min ago",
      status: "online",
    },
  ]}
  viewAllHref="/notifications"
/>
```

- 未读 dot：`absolute size-2 rounded-full bg-orange-400` + `animate-ping`
- Trigger：圆形 `size-11` Bell 按钮
- Panel：`w-[350px] h-[480px]` 滚动列表 + Footer 链接
- 列表项：Avatar + 标题 + 时间 `text-theme-xs text-gray-500`

## MultiSelect

**源**：`form/MultiSelect.tsx` — 标签 chips + 下拉多选。  
**推荐**：`Popover` + `Command`（shadcn）

可复制模板：`templates/ui/multi-select.tsx`

```tsx
import { MultiSelect } from "@/components/ui/multi-select";

<MultiSelect
  label="Departments"
  options={[
    { value: "product", label: "Product" },
    { value: "engineering", label: "Engineering" },
    { value: "marketing", label: "Marketing" },
  ]}
  defaultValue={["product", "engineering"]}
  onValueChange={setDepartments}
  placeholder="Select departments..."
  maxVisibleTags={3}
/>
```

- Trigger：`min-h-11 rounded-lg border` + chips `rounded-full bg-gray-100`
- 超出 `maxVisibleTags` 显示 `+N more`
- Panel：`PopoverContent` + `CommandInput` 可搜索
- 选中：`text-brand-500` + checkbox 风格 check
- 键盘：Command 内置过滤与选择

## FileUpload

**源**：`form/input/FileInput.tsx`

可复制模板：`templates/ui/file-upload.tsx`

```tsx
import { FileUpload } from "@/components/ui/file-upload";

<FileUpload
  label="Attachment"
  accept=".pdf,.png,.jpg"
  hint="PDF or image up to 10MB"
  onChange={(e) => setFile(e.target.files?.[0])}
/>
```

- 高度 `h-11`；`file:` 伪元素按钮 `bg-gray-50 hover:bg-gray-100`
- 错误态：`variant="error"` 或 `error` prop + `text-error-500` hint
- 禁用：`disabled:opacity-40`

## FileDropzone

**源**：`form/input/FileInput.tsx`（drag-drop 扩展）

可复制模板：`templates/ui/file-dropzone.tsx`

```tsx
import { FileDropzone } from "@/components/ui/file-dropzone";

<FileDropzone
  label="批量导入"
  accept=".csv,.xlsx"
  multiple
  files={files}
  onFilesSelected={handleSelect}
  onRemoveFile={handleRemove}
/>
```

- 虚线边框 `border-dashed rounded-xl`；拖拽激活 `border-brand-500`
- 文件列表含进度条 `Progress`、上传中 `Spinner`、移除按钮
- 与 `FileUpload` 互补：简单单文件用 `FileUpload`，批量/拖拽用 `FileDropzone`
- 错误态：`error` prop + 单项 `status: "error"`

## DatePicker

**源**：`form/date-picker.tsx`（flatpickr）  
**推荐**：shadcn `Calendar` + `Popover` — `templates/ui/date-picker.tsx`

```tsx
import { DatePicker } from "@/components/ui/date-picker";

<DatePicker
  label="Due date"
  value={dueDate}
  onValueChange={setDueDate}
  placeholder="yyyy-mm-dd"
/>

<DatePicker
  label="Date range"
  mode="range"
  value={range}
  onValueChange={setRange}
/>

<DatePicker
  label="Maintenance dates"
  selectionMode="multiple"
  unavailable={[new Date("2026-07-05")]}
  min={new Date("2026-07-01")}
  max={new Date("2026-07-31")}
/>
```

- Trigger：`h-11` + `CalendarIcon size-5` + `shadow-theme-xs`
- 选中日期：`bg-brand-500`（calendar.tsx）
- range：`numberOfMonths={2}`；in-range `bg-brand-50`
- Chakra 兼容命名：`selectionMode="single" | "range" | "multiple"`；旧 `mode="single" | "range"` 保留。
- Calendar inline：直接使用 `templates/ui/calendar.tsx`，支持 `size`、`selectionMode`、`disabled` matcher。
- 错误：`error` prop；禁用：`disabled`

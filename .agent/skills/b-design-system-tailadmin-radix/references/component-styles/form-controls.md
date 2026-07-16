# 高级表单控件

技术栈：**React + shadcn/ui + Radix + Tailwind v4**。本文件定义 TailAdmin-Radix 多项目复用表单输入家族，覆盖 mask、OTP、数字、金额、Secret、异步校验与字段状态。

## 读取顺序

1. `component-index.md` → Advanced Form 行
2. 本文件选能力族
3. 对应 `templates/ui/*.tsx` 可复制模板
4. `state-index.md` 查字段状态覆盖
5. `preview.html#advanced-form-controls` 视觉验收

## 字段状态契约

所有高级输入必须通过 `FormField` 或 `AsyncField` 包装，统一呈现：

| 状态 | 边框/环 | 文案色 | 辅助行为 |
|---|---|---|---|
| default | `border-gray-300` + brand focus ring | `text-gray-500` helper | — |
| required | 同上 | label 带 `*` | `aria-required` |
| optional | 同上 | label 带 `(optional)` | — |
| error | `border-error-500` + error ring | `text-error-500` | `role="alert"` |
| success | `border-success-500` | `text-success-500` | — |
| warning | `border-warning-500` | `text-warning-500` | — |
| validating | default 边框 | helper + 右侧 Spinner | `data-loading` |
| disabled | `opacity-40 bg-gray-100` | — | `cursor-not-allowed` |
| readonly | 无 hover 反馈 | — | `readOnly` |

## Form layout 级联

**模板**：`templates/ui/form-context.tsx` · `templates/ui/form-section.tsx` · `templates/ui/form-field.tsx`

`FormProvider` / `FormSection` 可级联：

| prop | 值 | 影响 |
|---|---|---|
| `layout` | vertical / horizontal / inline | FormField label 与控件排列 |
| `labelWidth` | sm / md / lg | horizontal 时 label 列宽 |
| `inputSkin` | outlined / filled / borderless / underlined | 子级 `Input` 默认皮肤 |
| `requiredMark` | required / optional | 未显式 `required` 时的星号/选填文案 |
| `scrollToFirstError` | boolean | 默认 `false`；开启后配合 `useFormSubmit` 提交失败滚动 |

```tsx
<FormSection layout="horizontal" labelWidth="md" inputSkin="filled" requiredMark="optional">
  <FormField label="集群名称"><Input /></FormField>
</FormSection>
```

校验失败滚动：`scrollToFirstError()` / `useFormSubmit({ scrollToFirstError: true })`（`templates/lib/use-scroll-to-first-error.ts`）；`FormField` error 时输出 `data-field-invalid`；`form-page-shell.tsx` `onSave` 返回 `false` 时亦可调用。

## AdvancedInput

**源**：`form/input/InputField.tsx` 扩展 → `templates/ui/advanced-input.tsx`

| 变体 | type / 特性 | 说明 |
|---|---|---|
| text | `text` | 默认 |
| search | `search` | 自动 prefix Search 图标 |
| password | `password` | 原生 type |
| url / email | `url` / `email` | 原生校验 + helper |
| prefix / suffix | slot | 图标、单位、操作按钮 |
| clearable | `clearable` | 有值时显示 × |
| copyable | `copyable` | 右侧 Copy 按钮 |
| counter | `counter={{value,max}}` | 字符计数右对齐 |
| unit | `unit` | 后缀单位文本 |

```tsx
<FormField label="Search tenants" required helper="Filter by name or ID">
  <AdvancedInput type="search" clearable placeholder="Search…" />
</FormField>
```

## NumericInput

**模板**：`templates/ui/numeric-input.tsx`

| format | 展示 | 约束 |
|---|---|---|
| integer | 整数 | `min` / `max` / stepper |
| decimal | 小数 | `precision` |
| currency | `Intl.NumberFormat` | `currency` prop |
| percent | 后缀 `%` | 0–100 或业务域 |

```tsx
<NumericInput format="currency" currency="USD" showStepper min={0} />
```

## MaskedInput

**模板**：`templates/ui/masked-input.tsx`

| preset | mask | paste normalize |
|---|---|---|
| phone | `(###) ###-####` | 仅数字 |
| id | `###-##-####` | 仅数字 |
| license | `XXXX-XXXX-XXXX-XXXX` | 字母数字 |
| ip | `###.###.###.###` | 数字与点 |
| cidr | `##.##.##.##/##` | CIDR |
| custom | `mask` prop | 业务定义 |

## OtpInput

**源**：`components/auth/OtpForm.tsx` → `templates/ui/otp-input.tsx`

- `length`: 4 / 6 / 8
- `groupSize`: 分组显示（如 3+3）
- 粘贴整段自动填充
- Backspace / Arrow 跳格
- `expired` + `resendPending` 态

## SecretInput

**模板**：`templates/ui/secret-input.tsx`

- masked / revealed 切换
- `copyOnce` + 审计提示
- `onRotate` / `onRevoke` 危险动作
- 等宽字体展示 API Key / token

## AsyncField

**模板**：`templates/ui/async-field.tsx`

| state | 场景 | UI |
|---|---|---|
| idle | 初始 | 普通字段 |
| validating | 唯一性 / 连通性 / schema | Spinner + "Checking…" |
| success | 校验通过 | success 文案 |
| warning | 软警告 | warning 文案 |
| error | 失败 | error + Retry 按钮 |

```tsx
<AsyncField
  label="Endpoint URL"
  state={state}
  error="Connection refused"
  onRetry={runProbe}
>
  <AdvancedInput type="url" />
</AsyncField>
```

## FormList {#formlist}

**模板**：`templates/ui/form-list.tsx` · **Hook**：`templates/lib/use-form-list.ts`

antd `Form.List` 等价 — 动态重复字段 compound。

| prop / API | 类型 | 说明 |
|---|---|---|
| `initialValue` / `min` / `max` | `T[]` / `number` | `useFormList` 选项 |
| `fields` / `values` | `FormListField<T>[]` / `T[]` | 稳定 `id` + 值数组 |
| `add` / `remove` / `move` / `replace` | fn | 增删移替换 |
| `FormListItems` | `renderItem(index, field, { remove })` | 渲染每项 |
| `FormListAdd` | `label?` | 添加按钮；受 `canAdd` 控制 |

```tsx
<FormList initialValue={[{ name: "" }]} min={1} max={5}>
  <FormListItems<{ name: string }>
    renderItem={(index, field, { remove }) => (
      <FormField label={`联系人 ${index + 1}`}>
        <Input defaultValue={field.value.name} />
        <Button type="button" variant="ghost" onClick={remove}>删除</Button>
      </FormField>
    )}
  />
  <FormListAdd label="添加联系人" />
</FormList>
```

## scrollToFirstError {#scrolltofirsterror}

**模板**：`templates/lib/use-scroll-to-first-error.ts`

| 导出 | 说明 |
|---|---|
| `scrollToFirstError(root?)` | 查询 `[data-field-invalid]` 并 `scrollIntoView` + focus |
| `useFormSubmit({ onValid, onInvalid, scrollToFirstError, formRef })` | 原生 `checkValidity` 失败时自动滚动 |

配合 `FormProvider scrollToFirstError` 或示例显式 `useFormSubmit({ scrollToFirstError: true })`。

## PasswordInput {#passwordinput}

**模板**：`templates/ui/password-input.tsx`

| prop | 类型 | 说明 |
|---|---|---|
| `showToggle` | `boolean?` | 显示/隐藏密码按钮；默认 `true` |
| 其余 | `InputProps` | 继承 `inputSkin`（FormContext 级联） |

登录密码场景；**不含** copy/rotate — 重密文用 `SecretInput`。

## FormFieldset {#formfieldset}

**模板**：`templates/ui/form-fieldset.tsx`

| prop | 类型 | 说明 |
|---|---|---|
| `legend` | `ReactNode?` | `<legend>` 分组标题 |
| `description` | `ReactNode?` | 分组说明 |
| `disabled` | `boolean?` | 禁用整组子控件 |

语义分组；视觉卡片分组仍用 `FormSection`。

## RadioButtonGroup {#radiobuttongroup}

**模板**：`templates/ui/radio-button-group.tsx`

antd `Radio.Button` 等价 — 按钮外观单选。

| prop | 类型 | 说明 |
|---|---|---|
| `orientation` | `horizontal \| vertical?` | 排列方向 |
| `size` | `sm \| md \| lg?` | 按钮尺寸 |
| `block` | `boolean?` | 全宽等分按钮组 |
| `RadioButton` | `value` + children | 单项；选中 `data-[state=checked]:ring-brand-500` |

```tsx
<RadioButtonGroup defaultValue="a" block>
  <RadioButton value="a">日</RadioButton>
  <RadioButton value="b">周</RadioButton>
  <RadioButton value="c">月</RadioButton>
</RadioButtonGroup>
```

## 可复制模板索引

| 模板 | 路径 |
|---|---|
| FormField | `templates/ui/form-field.tsx` |
| FormList | `templates/ui/form-list.tsx` |
| useFormList | `templates/lib/use-form-list.ts` |
| useScrollToFirstError | `templates/lib/use-scroll-to-first-error.ts` |
| PasswordInput | `templates/ui/password-input.tsx` |
| FormFieldset | `templates/ui/form-fieldset.tsx` |
| RadioButtonGroup | `templates/ui/radio-button-group.tsx` |
| AdvancedInput | `templates/ui/advanced-input.tsx` |
| NumericInput | `templates/ui/numeric-input.tsx` |
| MaskedInput | `templates/ui/masked-input.tsx` |
| OtpInput | `templates/ui/otp-input.tsx` |
| SecretInput | `templates/ui/secret-input.tsx` |
| AsyncField | `templates/ui/async-field.tsx` |

## Cascader {#cascader}

**模板**：`templates/ui/hierarchical-picker/cascader.tsx`

| prop | 类型 | 说明 |
|---|---|---|
| `options` | `HierarchicalNode[]` | 树形数据源 |
| `value` / `onChange` | `string[]` | 受控路径 id 数组 |
| `loadData` | `LoadDataFn?` | 异步加载子节点 |
| `multiple` | `boolean?` | 多路径选择 |
| `changeOnSelect` | `boolean?` | 允许选中中间层 |
| `showSearch` | `boolean?` | 列内搜索 |
| `inputSkin` | `outlined \| filled \| borderless \| underlined` | Trigger 皮肤 |

## TreeSelect {#treeselect}

**模板**：`templates/ui/hierarchical-picker/tree-select.tsx`

| prop | 类型 | 说明 |
|---|---|---|
| `treeData` | `HierarchicalNode[]` | 树形数据源 |
| `value` / `onChange` | `string \| string[]` | 单选或多选 key |
| `treeCheckable` | `boolean?` | 勾选模式 |
| `showCheckedStrategy` | `CheckStrategy?` | `child` / `parent` / `all` |
| `loadData` | `LoadDataFn?` | 异步加载子节点 |
| `showSearch` | `boolean?` | 面板内搜索 |
| `inputSkin` | `outlined \| filled \| borderless \| underlined` | Trigger 皮肤 |

## TimePicker {#timepicker}

**模板**：`templates/ui/time-picker.tsx`

| prop | 类型 | 说明 |
|---|---|---|
| `value` / `onChange` | `Date?` | 受控时间值（日期部分忽略，仅取时分秒） |
| `format` | `string?` | 显示格式，默认 `HH:mm` |
| `showSeconds` | `boolean?` | 是否显示秒列 |
| `minuteStep` / `secondStep` | `number?` | 步进间隔 |
| `disabledHours` / `disabledMinutes` | `fn?` | 禁用特定时/分 |
| `range` | `[Date, Date]?` | 可选时间范围 |
| `inputSkin` | `outlined \| filled \| borderless \| underlined` | Trigger 皮肤 |

Popover + 三列 ScrollArea（时/分/秒）；选中态 `bg-brand-50`。

## Mentions {#mentions}

**模板**：`templates/ui/mentions.tsx`

| prop | 类型 | 说明 |
|---|---|---|
| `value` / `onChange` | `string` | 受控文本 |
| `options` | `{ value, label, avatar? }[]` | @ 候选列表 |
| `onSearch` | `(query: string) => void?` | 远程搜索回调 |
| `prefix` | `string?` | 触发前缀，默认 `@` |
| `rows` | `number?` | Textarea 行数 |
| `inputSkin` | `outlined \| filled \| borderless \| underlined` | 输入框皮肤 |

光标前 `@` 检测 → Popover 列表 → 选中插入 `@label `。

## Rating {#rating}

**模板**：`templates/ui/rating.tsx`

| prop | 类型 | 说明 |
|---|---|---|
| `value` / `onChange` | `number` | 当前评分（0～count） |
| `count` | `number?` | 星数，默认 5 |
| `allowHalf` | `boolean?` | 半星评分 |
| `readOnly` | `boolean?` | 只读展示 |
| `size` | `sm \| md \| lg?` | 星标尺寸 |

`role="slider"`；键盘 ArrowLeft/Right；`readOnly` 时无交互。

## ColorPicker {#colorpicker}

**模板**：`templates/ui/color-picker.tsx` · **peer**：`react-colorful` ^5.x

| prop | 类型 | 说明 |
|---|---|---|
| `value` / `onChange` | `string` | hex 色值 |
| `format` | `hex \| rgb \| hsl?` | 输出格式 |
| `presets` | `string[]?` | preset 色块行 |
| `trigger` | `swatch \| input?` | 触发器形态 |
| `showInput` | `boolean?` | 是否显示 hex 文本框 |

Popover + `HexColorPicker`；preset 色块快速选取。

## Editable {#editable}

**模板**：`templates/ui/editable.tsx`

| prop | 类型 | 说明 |
|---|---|---|
| `value` / `onChange` | `string` | 受控文本 |
| `onSubmit` / `onCancel` | `fn?` | 提交/取消回调 |
| `submitOnBlur` | `boolean?` | 失焦提交，默认 `true` |
| `placeholder` | `string?` | 空值占位 |

导出 `Editable`（单行）+ `EditableTextarea`（多行）；点击进入 borderless Input。

## DatePicker showTime {#datepicker-showtime}

**模板**：`templates/ui/date-picker.tsx`（扩展，非新组件）

| prop | 类型 | 说明 |
|---|---|---|
| `showTime` | `boolean \| { format?, minuteStep? }?` | 单选模式下 Calendar 底部嵌入 TimePicker 列 |

选中日期后合并 time 到 `Date` 对象 `onValueChange`；仅 `selectionMode="single"` 生效。仅日期场景继续用 DatePicker 不带 `showTime`；仅时间用 TimePicker — 见 `decision-matrix.md`。

## Preview 验收

- section：`preview.html#advanced-form-controls`
- 截图：`preview-screenshots/advanced-form-light.png`、`advanced-form-dark.png`、`advanced-form-mobile-light.png`
- 必须覆盖：prefix/suffix、currency stepper、phone mask、OTP 6 位、secret reveal、async validating
- 禁止：窄列、文本裁切、大面积空白

## 演化记录

| 轮次 | 变更 |
|---|---|
| G21 DS-045 | 首版七模板 + reference + preview section |
| PR-E Batch E | FormList、scrollToFirstError、PasswordInput、FormFieldset、RadioButtonGroup |

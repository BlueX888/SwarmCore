# 布局模式 — Form Flow

典型路由：`/add-product`、`/profile`、`/create-invoice`

## 结构

```tsx
<AppLayout>
  <form className="mx-auto flex max-w-3xl flex-col gap-6">
    <div>
      <h1 className="text-xl font-semibold">Add Product</h1>
      <p className="text-theme-sm text-gray-500">Fill in product details</p>
    </div>

    <ComponentCard title="Basic Info">
      <div className="grid gap-5 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <Label>Name</Label>
          <Input />
        </div>
        <div>
          <Label>Category</Label>
          <Select />
        </div>
        <div>
          <Label>Price</Label>
          <Input type="number" />
        </div>
      </div>
    </ComponentCard>

    <ComponentCard title="Media">
      <FileUpload label="Product image" accept="image/*" hint="PNG or JPG up to 5MB" />
    </ComponentCard>

    <ComponentCard title="Tags">
      <MultiSelect
        label="Departments"
        options={departmentOptions}
        value={departments}
        onValueChange={setDepartments}
      />
    </ComponentCard>

    <div className="flex justify-end gap-3">
      <Button variant="outline" type="button">Cancel</Button>
      <Button variant="primary" type="submit">Save</Button>
    </div>
  </form>
</AppLayout>
```

## 表单规则

- 控件统一 `h-11`
- 字段间距 `gap-5`
- 错误：`FormMessage` + Input error 态
- 必填：Label 后 `text-error-500` *
- 长表单：多 `ComponentCard` 分段 + 底部 sticky actions（可选）

## 布局变体

**源**：`pages/Forms/FormLayout.tsx`

- 单列表单：`max-w-2xl`
- 双列：`sm:grid-cols-2`
- 带侧栏预览：主表 `2/3` + 预览 `1/3`

## 校验

推荐 `react-hook-form` + `zod`；提交失败 focus 第一个错误字段。

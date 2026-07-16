# ImageCompare 配置 Diff

发布前后 / 配置变更视觉对比（对标 PrimeVue ImageCompare）：

```
PageHeader
├── 版本信息 Badge
├── ImageCompare（beforeSrc / afterSrc）
└── DescriptionList 变更摘要（可选）
```

## 组件

- `image-compare.tsx`

## 场景

- DevOps 配置 Diff 预览
- 截图回归对比
- 主题切换前后

## 决策

- 多图画廊 → `ImagePreview` + `Masonry`
- 单图展示 → `image.tsx`

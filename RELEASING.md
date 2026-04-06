# 发布说明

## 首次开源前建议

1. 确认仓库名称、简介和截图
2. 检查 `LICENSE`、`README.md`、`.gitignore`
3. 检查版本号是否正确
4. 确认 `build.ps1` 和 GitHub Actions 都能正常打包

## 本地构建

```powershell
.\build.ps1
```

## 发布新版本

1. 更新 `autoclicker/__init__.py` 中的 `APP_VERSION`
2. 提交并推送到 `main`
3. 创建标签，例如：

```powershell
git tag v1.0.0
git push origin v1.0.0
```

4. GitHub Actions 会自动：
   - 生成图标资源
   - 安装依赖
   - 使用 PyInstaller 打包
   - 上传 Artifact
   - 在标签构建时创建 GitHub Release 并附带打包产物

## 建议补充

- 在仓库主页添加软件截图
- 为 Release 写更新日志
- 后续可增加 `CHANGELOG.md`

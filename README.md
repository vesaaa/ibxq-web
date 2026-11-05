# ibxq-web

爱伴星球（IBXQ）官网：<https://ibxq.com>

纯静态站点，没有构建步骤，直接部署在 Cloudflare Pages。

## 目录

| 文件 | 说明 |
|---|---|
| `index.html` | 整个网站，CSS 和 JS 都写在里面 |
| `fonts/` | 只包含页面用到的字的字体子集，由脚本生成 |
| `favicon.svg`、`favicon-32.png`、`apple-touch-icon.png` | 网站图标 |
| `og.png` | 分享链接时显示的预览图（1200×630），源文件是 `scripts/og.html` |
| `_headers` | Cloudflare Pages 的缓存和安全响应头 |
| `scripts/build-fonts.py` | 重新生成字体子集 |

## 部署到 Cloudflare Pages

1. Cloudflare 后台 → Workers & Pages → 创建 → Pages → 连接到 Git，选择本仓库
2. 框架预设选「无」，构建命令留空，构建输出目录填 `/`
3. 部署完成后，在项目的「自定义域」里添加 `ibxq.com` 和 `www.ibxq.com`

之后每次推送到 `main` 分支都会自动发布。

## 修改文案后

字体只包含页面上已有的字。改了 `index.html` 里的文字后，重新生成字体，否则新加的字会显示成系统字体：

```bash
python3 scripts/build-fonts.py
```

脚本只用 Python 标准库，需要能访问 Google Fonts。

## 产品版本号

产品卡片上的版本号写在 `index.html` 里作为默认值。访客打开页面时，页面会向 GitHub 查询各仓库的最新发行版并替换显示，结果在访客浏览器里缓存 6 小时。新增产品时，在版本标签上加 `data-repo="仓库名"` 即可。

# 公開手順とクロールのための構成

## このパッケージ

- `README.md`：GitHubリポジトリでの入口。
- `content/`：全54ページのMarkdown。GitHub上で閲覧可能。
- `data/catalog.json`：全掲載情報の編集元。
- `build.py`：Python標準ライブラリだけでHTML・Markdownを生成し、リンク等を検証。
- `_site/`：生成済みの静的HTMLプレビュー。公開前に実URLで再生成する。
- `.github/workflows/pages.yml`：GitHub Pages用ビルド・公開設定。
- `site-config.json`：サイト名・更新日・手動公開用URL設定。

PDF原本、社内確認台帳、未確定情報、旧素案の進捗メモはパッケージに含めていません。

## 推奨する公開方法：GitHub Pages

1. `inbyte-product-guide`フォルダーの**中身**をGitHubリポジトリのルートへ配置する。フォルダー自体を一段深く置かない。
2. `.github/workflows/pages.yml`も含めて配置する。ドットで始まる隠しフォルダーが漏れないよう確認する。
3. リポジトリのSettings → Pages → Build and deploymentで、Sourceを**GitHub Actions**に設定する。
4. `main`ブランチへ反映するか、Actionsでワークフローを手動実行する。既定ブランチが別名ならYAMLの`branches`も合わせる。
5. ワークフローがGitHub Pagesの実URLを取得し、canonical、JSON-LD、XMLサイトマップを生成する。公開されるのは`_site/`だけ。
6. Actions完了後の公開URLでトップ・製品ページ・`sitemap.xml`を開く。
7. GitHubリポジトリのAbout欄のWebsiteに公開URLを設定する。公式サイト側からも「用途から選ぶ製品ガイド」としてリンクする。
8. Search Consoleなどで公開先を確認し、公開URLの`sitemap.xml`を送信する。

この設定を配置して実行するとサイトを公開します。今回の納品ではリポジトリ作成・アップロード・ワークフロー実行は行っていません。

## 公開URLと生成物

公開先未定のため、同梱プレビューでは架空のcanonical、JSON-LDのページURL、XMLサイトマップを出力していません。本文・HTMLリンク・CSSは完成しています。

GitHub Pages公開時は`actions/configure-pages`の`base_url`を環境変数として渡し、以下を自動生成します。

- 各ページの自己参照canonical。
- 公開先の絶対URLを使うXMLサイトマップ。
- Organization、WebPage／CollectionPage、BreadcrumbList、製品ページのProduct情報。
- `robots.txt`のSitemap案内。

`--production`は実URLがない場合にエラーで停止します。プレースホルダーURLのまま公開する設定にはしていません。

## 独自ドメインや公式サイト配下で公開する場合

GitHub Pagesの独自ドメインはSettings → Pagesで設定します。URL変更後に再ビルドしてください。GitHub Pagesの設定とDNSはこのパッケージでは変更しません。

ほかの静的ホスティングや公式サイト配下で公開する場合は、`site-config.json`の`base_url`へ実際の公開ディレクトリURLを指定し、次を実行します。

```text
python build.py --production
```

生成された`_site/`の中身を、そのURLに対応する公開ディレクトリへ配置してください。HTML以外の管理用ファイルをサイト直下へ丸ごと置く必要はありません。

同じ内容を複数ドメインへ公開する場合は、代表にしたい公開先を決め、そのURLをcanonicalとサイトマップで一貫させます。内容が違う既存製品ページへ機械的にcanonicalを向けないでください。

## robots.txtの配置上の注意

検索クローラーが読むrobots.txtは、**各ホストのルート**にあるものです。

- 独自ドメインのルートで公開：生成した`robots.txt`をそのまま配置可能。
- `owner.github.io/repository/`のようなプロジェクト配下：`/repository/robots.txt`はホスト全体のクロール規則にはなりません。ホストのルートのrobots.txtを管理できる場合は既存規則と統合してください。
- 公式サイトのサブディレクトリ：既存ルートrobots.txtを上書きせず、対象パスが遮断されていないか確認します。

ルートrobots.txtを編集できなくても、公開HTMLのリンクとSearch Consoleへのサイトマップ送信で発見を促せます。

## 更新方法

1. `data/catalog.json`の本文・仕様・出典を修正する。
2. 実際に情報が変わった日を`site-config.json`の`updated`と該当製品の`updated`へ設定する。
3. `python build.py`でローカルプレビューとMarkdownを再生成する。
4. 原稿と生成されたMarkdownをコミットする。GitHub ActionsがHTMLを再生成して公開する。

`content/*.md`と`_site/*.html`は生成物です。直接編集すると次回ビルドで上書きされます。

P1000 5Gの発売状況、SVI-8004の垂直画角、性能評価の条件、価格・契約条件は、根拠が更新された段階で反映してください。資料中の「99.9%」「97%以上」「80%以上抑止」等は無条件の保証として公開原稿へ入れていません。

## 実装したクロール対応

- 本文・仕様表・リンクは初期HTMLに含まれ、JavaScript実行やクリック操作なしで読める。
- 各製品・用途・比較に固有のURL、title、description、H1。
- 一覧、関連製品、用途、パンくず、HTMLサイトマップで相互に接続。
- ページURLはASCIIの固定パス。検索条件やハッシュで本文を切り替えない。
- XMLサイトマップに公開ページだけを列挙し、正規URLと一致させる。
- 構造化データは表示内容に対応する名称・概要等だけを使用。架空の評価、在庫、価格、レビューは付けない。
- モバイル対応、軽量CSS、見出しと通常のHTML表、スキップリンク。
- 404ページはnoindex。正規の製品・用途ページはindex,follow。

構造化データはリッチリザルトやAIでの推薦を保証しません。Productに価格・レビューを無理に追加していないため、特定のリッチリザルトの要件を満たさない場合があります。クロール・インデックス・順位・AI引用は別段階であり、どれも公開だけでは保証されません。

## 公開後の確認

- HTMLが200で取得でき、存在しないURLは404を返す。
- canonicalが実URLと一致し、仮ドメインや以前の公開先が残っていない。
- XMLサイトマップのURLがすべて開ける。
- robots.txt、noindex、認証、CDN設定で対象ページを遮断していない。
- 公式サイトからの案内リンクがある。
- Search Consoleで検出・登録状況を確認する。未登録の場合は理由を調べる。

## 設計の根拠

- [Google：クロール可能なリンク](https://developers.google.com/search/docs/crawling-indexing/links-crawlable)
- [Google：正規URLの指定](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
- [Google：URL構造](https://developers.google.com/search/docs/crawling-indexing/url-structure)
- [Google：AI機能とウェブサイト](https://developers.google.com/search/docs/appearance/ai-features)
- [GitHub：Pagesのカスタムワークフロー](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

確認日：2026-09-15。

# ShellArc: Animation Production Pipeline Server Framework
# ShellArc: アニメーション制作パイプラインサーバーフレームワーク

> ### **Development Branch / 開発ブランチ**: `dev_2027`

---

## [日本語 / Japanese]

### プロジェクト概要
ShellArcは、アニメーション制作パイプラインを統合・効率化するためのサーバーフレームワークです。
本ロードマップおよびアジェンダは **`dev_2027`** ブランチでの開発を対象としています。各タスクには **[緊急度 / スケール (1〜5)]** を付与し、優先度を視覚化しています。

---

### 開発アジェンダとタスク一覧

#### 1. コード品質 (Code Quality)
- 包括的な単体テスト（ユニットテスト）の実装 [緊急度: 5 / スケール: 4]
- 操作可能な包括的なダミーUIの実装 [緊急度: 4 / スケール: 3]
- CI/CDテスト自動化の確立 [緊急度: 5 / スケール: 3]
- ドキュメント文字列（Docstring）の改善 [緊急度: 4 / スケール: 1]
- 可読性の低いコードや過度に長いスクリプトのリファクタリング [緊急度: 4 / スケール: 3]

#### 2. 数学とデータサイエンス (Math and Data Science)
- ShellArcコアモジュールへの「ShellArc Railgun Architecture Model」の組み込み [緊急度: 4 / スケール: 5]
  - (https://github.com/shinonome-MiDUki/Shell_Arc_Railgun_scheduler)

#### 3. クラウドとインフラ (Cloud and Infrastructure)
- AWS Deep Glacierを活用した自動バックアップの実装 [緊急度: 3 / スケール: 2]
- デスクトップアプリおよびローカルプログラムとの安全なHTTPS通信の許可 [緊急度: 3 / スケール: 4]
- 開発イテレーション改善のためのDocker設定の見直し [緊急度: 4 / スケール: 1]

#### 4. フォーマットとデータ構造 (Format and Data Structure)
- パフォーマンス向上と柔軟性強化のための、サブプロセス・コマンドからPyGit2への移行 [緊急度: 2 / スケール: 4]
- ShellArc管理下プロジェクトにおけるプロジェクト記述データフォーマットの標準化 [緊急度: 3 / スケール: 5]

#### 5. デスクトップアプリケーション (Desktop Applications)
- 「Shell DELTA」のShellArcエコシステムへの統合 [緊急度: 4 / スケール: 4]
  - (https://github.com/shinonome-MiDUki/Shell_DELTA)
- Shell DELTAのコンポジティング機能の拡張とGLSLサポートの改善 [緊急度: 4 / スケール: 2]
- Shell DELTAへのPythonスクリプティング実装 [緊急度: 3 / スケール: 3]
- ShellArcデスクトップアプリのUI改善 [緊急度: 4 / スケール: 2]
- プロジェクト管理機能とプロジェクト進捗視覚化の拡張 [緊急度: 4 / スケール: 5]

#### 6. グラフィックスとメディア (Graphics and Media)
- 独自コーデックフォーマット「NUDEC」のGPU使用率と効率性の改善 [緊急度: 3 / スケール: 4]
- 周辺オーディオシステムとの同期改善 [緊急度: 4 / スケール: 3]
- `.nuanim` クラウドレンダリングのためのCIワークフローの確立 [緊急度: 3 / スケール: 2]

#### 7. AIと機械学習 (AI and Machine Learning)
- 更新に応じたRAG自動更新ワークフローの確立 [緊急度: 4 / スケール: 1]
- RunpodとComfyUIを活用した自動カラーリングシステムの構築 [緊急度: 3 / スケール: 3]
- エージェント駆動によるShellArc拡張・カスタマイズ開発に向けたスキルシートの改善 [緊急度: 3 / スケール: 1]

#### 8. 自動化サーバー (Automation Server)
- Item Action自動スケジューリングサーバーのプロダクションレベルへの引き上げ [緊急度: 3 / スケール: 2]

---

## [English / 英語]

### Project Overview
ShellArc is an animation production pipeline server framework designed to integrate and streamline production workflows. 
This roadmap and agenda target development on the **`dev_2027`** branch. Each task is annotated with **[Urgency / Scale (1-5)]** to visualize priorities.

---

### Development Agenda & Tasks

#### 1. Code Quality
- Implementation of comprehensive unit tests [Urgency: 5 / Scale: 4]
- Implementation of a comprehensive dummy-operatable UI [Urgency: 4 / Scale: 3]
- Establish CI/CD test automation [Urgency: 5 / Scale: 3]
- Improve docstrings [Urgency: 4 / Scale: 1]
- Refactor codes with low readability and excessively lengthy scripts [Urgency: 4 / Scale: 3]

#### 2. Math and Data Science
- Embed ShellArc Railgun Architecture Model into the ShellArc core module [Urgency: 4 / Scale: 5]
  - (https://github.com/shinonome-MiDUki/Shell_Arc_Railgun_scheduler)

#### 3. Cloud and Infrastructure
- Implement auto-backup on AWS Deep Glacier [Urgency: 3 / Scale: 2]
- Allow safe HTTPS communication with desktop apps and local programs [Urgency: 3 / Scale: 4]
- Revise Docker configurations for improving development iteration [Urgency: 4 / Scale: 1]

#### 4. Format and Data Structure
- Migrate from subprocess commands to PyGit2 for better performance and higher flexibility [Urgency: 2 / Scale: 4]
- Standardize project description data format for projects under ShellArc's management [Urgency: 3 / Scale: 5]

#### 5. Desktop Applications
- Incorporate Shell DELTA into the ShellArc eco-system [Urgency: 4 / Scale: 4]
  - (https://github.com/shinonome-MiDUki/Shell_DELTA)
- Extend compositing features of Shell DELTA and improve GLSL support [Urgency: 4 / Scale: 2]
- Implement Python scripting for Shell DELTA [Urgency: 3 / Scale: 3]
- Improve UI of the ShellArc Desktop app [Urgency: 4 / Scale: 2]
- Extend project management features and project progress visualization [Urgency: 4 / Scale: 5]

#### 6. Graphics and Media
- Improve GPU usage and efficiency of the NUDEC codec format [Urgency: 3 / Scale: 4]
- Improve synchronization with surrounding audio systems [Urgency: 4 / Scale: 3]
- Establish CI workflow for `.nuanim` cloud rendering [Urgency: 3 / Scale: 2]

#### 7. AI and Machine Learning
- Establish an automation workflow for RAG updates upon updates [Urgency: 4 / Scale: 1]
- Establish an auto-coloring system via Runpod and ComfyUI [Urgency: 3 / Scale: 3]
- Improve skill sheets for agent-driven ShellArc extension and customization developments [Urgency: 3 / Scale: 1]

#### 8. Automation Server
- Improve Item Action auto-scheduling server to production level [Urgency: 3 / Scale: 2]

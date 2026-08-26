# ShellArc: Animation Production Pipeline Server Framework
# ShellArc: アニメーション制作パイプラインサーバーフレームワーク

> ### **Development Branch / 開発ブランチ**: `dev_2027`

---

## [日本語 / Japanese]

### プロジェクト概要
ShellArcは、アニメーション制作パイプラインを統合・効率化するためのサーバーフレームワークです。

### 開発アジェンダとタスク一覧

#### 1. コード品質 (Code Quality)
- 包括的な単体テスト（ユニットテスト）の実装
- 操作可能な包括的なダミーUIの実装
- CI/CDテスト自動化の確立
- ドキュメント文字列（Docstring）の改善
- 可読性の低いコードや過度に長いスクリプトのリファクタリング

#### 2. 数学とデータサイエンス (Math and Data Science)
- ShellArcコアモジュールへの「ShellArc Railgun Architecture Model」の組み込み
  - (https://github.com/shinonome-MiDUki/Shell_Arc_Railgun_scheduler)

#### 3. クラウドとインフラ (Cloud and Infrastructure)
- AWS Deep Glacierを活用した自動バックアップの実装
- デスクトップアプリおよびローカルプログラムとの安全なHTTPS通信の許可
- 開発イテレーション改善のためのDocker設定の見直し

#### 4. フォーマットとデータ構造 (Format and Data Structure)
- パフォーマンス向上と柔軟性強化のための、サブプロセス・コマンドからPyGit2への移行
- ShellArc管理下プロジェクトにおけるプロジェクト記述データフォーマットの標準化

#### 5. デスクトップアプリケーション (Desktop Applications)
- 「Shell DELTA」のShellArcエコシステムへの統合
  - (https://github.com/shinonome-MiDUki/Shell_DELTA)
- Shell DELTAのコンポジティング機能の拡張とGLSLサポートの改善
- Shell DELTAへのPythonスクリプティング実装
- ShellArcデスクトップアプリのUI改善
- プロジェクト管理機能とプロジェクト進捗視覚化の拡張

#### 6. グラフィックスとメディア (Graphics and Media)
- 独自コーデックフォーマット「NUDEC」のGPU使用率と効率性の改善
- 周辺オーディオシステムとの同期改善
- `.nuanim` クラウドレンダリングのためのCIワークフローの確立

#### 7. AIと機械学習 (AI and Machine Learning)
- 更新に応じたRAG自動更新ワークフローの確立
- RunpodとComfyUIを活用した自動カラーリングシステムの構築
- エージェント駆動によるShellArc拡張・カスタマイズ開発に向けたスキルシートの改善

#### 8. 自動化サーバー (Automation Server)
- Item Action自動スケジューリングサーバーのプロダクションレベルへの引き上げ

---

## [English / 英語]

### Project Overview
ShellArc is an animation production pipeline server framework designed to integrate and streamline production workflows.

### Development Agenda & Tasks

#### 1. Code Quality
- Implementation of comprehensive unit tests
- Implementation of a comprehensive dummy-operatable UI
- Establish CI/CD test automation
- Improve docstrings
- Refactor codes with low readability and excessively lengthy scripts

#### 2. Math and Data Science
- Embed ShellArc Railgun Architecture Model into the ShellArc core module
  - (https://github.com/shinonome-MiDUki/Shell_Arc_Railgun_scheduler)

#### 3. Cloud and Infrastructure
- Implement auto-backup on AWS Deep Glacier
- Allow safe HTTPS communication with desktop apps and local programs
- Revise Docker configurations for improving development iteration

#### 4. Format and Data Structure
- Migrate from subprocess commands to PyGit2 for better performance and higher flexibility
- Standardize project description data format for projects under ShellArc's management

#### 5. Desktop Applications
- Incorporate Shell DELTA into the ShellArc eco-system
  - (https://github.com/shinonome-MiDUki/Shell_DELTA)
- Extend compositing features of Shell DELTA and improve GLSL support
- Implement Python scripting for Shell DELTA
- Improve UI of the ShellArc Desktop app
- Extend project management features and project progress visualization

#### 6. Graphics and Media
- Improve GPU usage and efficiency of the NUDEC codec format
- Improve synchronization with surrounding audio systems
- Establish CI workflow for `.nuanim` cloud rendering

#### 7. AI and Machine Learning
- Establish an automation workflow for RAG updates upon updates
- Establish an auto-coloring system via Runpod and ComfyUI
- Improve skill sheets for agent-driven ShellArc extension and customization developments

#### 8. Automation Server
- Improve Item Action auto-scheduling server to production level

# Project instructions

- 每完成一个可交付改动批次，必须在交付用户前创建 Git commit；不得把用户文件或无关改动混入提交。
- 每次修改代码、模板、样式、配置、数据迁移或行为文档，都必须同步新增或更新相关测试。
- 交付前必须使用 Python 3.13 运行完整测试 `py -3.13 manage.py test -v 1`，并确保全部通过。
- 交付前还必须通过 `py -3.13 manage.py check`、`py -3.13 manage.py makemigrations --check --dry-run` 和 `git diff --check`。
- 未跟踪的用户文件不得删除、改名、暂存或提交；只显式暂存本次改动文件。

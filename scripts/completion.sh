#!/bin/bash
# ============================================================
# Chimera Bash 自动补全脚本
# 安装: source chimera_completion.sh
# 永久: cp chimera_completion.sh /etc/bash_completion.d/chimera
# ============================================================

_chimera_completion() {
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # 主命令
    local commands="scan fingerprint migrate serve list inspect stats rollback doctor"

    # 子命令
    case "${prev}" in
        chimera|cli.py)
            COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
            return 0
            ;;
        list)
            COMPREPLY=( $(compgen -W "games engines paths" -- "${cur}") )
            return 0
            ;;
        fingerprint|migrate|rollback)
            # 补全路径
            COMPREPLY=( $(compgen -d -- "${cur}") )
            # 也补全常用游戏路径
            local games=$(ls /mnt/hgfs/common/ 2>/dev/null | sed 's/ /\\ /g')
            COMPREPLY+=( $(compgen -W "${games}" -- "${cur}") )
            return 0
            ;;
    esac

    # 默认补全命令
    COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
    return 0
}

# 注册补全函数
complete -F _chimera_completion chimera
complete -F _chimera_completion python3
complete -F _chimera_completion cli.py

echo "Chimera 自动补全已加载"

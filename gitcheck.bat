echo "=== Git 连接状态检查 ==="
echo "1. 远程仓库配置："
git remote -v

echo "2. 当前分支："
git branch

echo "3. 网络连接测试："
git ls-remote origin HEAD

echo "4. 用户配置："
echo "用户名: $(git config user.name)"
echo "邮箱: $(git config user.email)"

echo "5. 认证方式："
git config credential.helper
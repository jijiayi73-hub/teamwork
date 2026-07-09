#!/bin/bash
# 配置 Docker 镜像加速

echo '=== 配置 Docker 镜像加速 ==='

sudo mkdir -p /etc/docker

sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://dockerproxy.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://docker.nju.edu.cn"
  ],
  "max-concurrent-downloads": 10,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  }
}
EOF

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker

echo '✅ Docker 镜像加速配置完成'
docker info | grep -A 5 'Registry Mirrors'

echo ''
echo '=== 开始构建 Docker 镜像 ==='
cd /opt/inner-garden
docker compose -f docker-compose.prod.yml build

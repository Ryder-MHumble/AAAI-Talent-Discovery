"""AMiner学者搜索API集成工具"""

import httpx
import logging
from typing import Optional, Dict, List, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


class AMinerAPI:
    """
    AMiner学者搜索API客户端
    
    用于：
    1. 学者身份验证 - 通过名字和机构匹配学者
    2. 信息补充 - 获取学者的研究兴趣、履历等额外信息
    3. 人名校验 - 验证候选人的真实身份
    """
    
    BASE_URL = "https://datacenter.aminer.cn/gateway/open_platform/api"
    ENDPOINTS = {
        "person_search": "/person/search",
        "person_detail": "/person/detail"
    }
    
    def __init__(self, api_key: str = None):
        """
        初始化AMiner API客户端
        
        Args:
            api_key: AMiner API密钥（从环境变量获取，或直接传入）
        """
        self.api_key = api_key or getattr(settings, 'AMINER_API_KEY', None)
        if not self.api_key:
            logger.warning("[AMiner] 未配置API密钥，功能将被禁用")
        self.timeout = 30.0
    
    async def search_scholar(
        self,
        name: str,
        organization: Optional[str] = None,
        offset: int = 0,
        size: int = 10
    ) -> Optional[Dict[str, Any]]:
        """
        搜索学者信息
        
        Args:
            name: 学者姓名（支持中英文）
            organization: 所属机构（可选）
            offset: 分页偏移
            size: 返回结果数量
            
        Returns:
            包含搜索结果的字典，如果失败返回None
            
        示例返回结构:
        {
            "status": 0,
            "data": {
                "hits": [
                    {
                        "id": "xxx",
                        "name": "John Doe",
                        "name_cn": "约翰·多",
                        "org": "Stanford University",
                        "org_cn": "斯坦福大学",
                        "interests": ["Machine Learning", "AI"],
                        "email": "john@stanford.edu",
                        ...
                    }
                ],
                "total": 150
            }
        }
        """
        if not self.api_key:
            logger.warning("[AMiner] API密钥未配置，跳过学者搜索")
            return None
        
        try:
            # 构建请求体
            payload = {
                "name": name,
                "offset": offset,
                "size": size
            }
            
            if organization:
                payload["org"] = organization
            
            headers = {
                "Content-Type": "application/json;charset=utf-8",
                "Authorization": self.api_key
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.BASE_URL}{self.ENDPOINTS['person_search']}",
                    json=payload,
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"[AMiner] 搜索成功: {name} - 找到{len(result.get('data', {}).get('hits', []))}个结果")
                    return result
                else:
                    logger.error(f"[AMiner] 搜索失败 - 状态码: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"[AMiner] 搜索异常: {str(e)}")
            return None
    
    async def get_person_detail(self, person_id: str) -> Optional[Dict[str, Any]]:
        """
        获取学者详细信息
        
        Args:
            person_id: AMiner中的学者ID
            
        Returns:
            包含详细信息的字典，如果失败返回None
        """
        if not self.api_key:
            return None
        
        try:
            headers = {
                "Authorization": self.api_key
            }
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}{self.ENDPOINTS['person_detail']}",
                    params={"id": person_id},
                    headers=headers
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"[AMiner] 获取详情成功: {person_id}")
                    return result
                else:
                    logger.error(f"[AMiner] 获取详情失败 - 状态码: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"[AMiner] 获取详情异常: {str(e)}")
            return None
    
    async def validate_and_enrich(
        self,
        name: str,
        affiliation: str,
        email: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        验证候选人身份并补充信息
        
        这是一个高级方法，结合搜索和验证逻辑：
        1. 使用姓名+机构搜索学者
        2. 使用semantic matching验证匹配度
        3. 提取关键信息如interests、email等
        
        Args:
            name: 候选人英文姓名
            affiliation: 候选人所属机构
            email: 候选人邮箱（可选，用于额外验证）
            
        Returns:
            包含验证和补充信息的字典
            {
                "is_verified": True/False,
                "aminer_id": "xxx",
                "name_cn": "xxx",
                "interests": ["AI", "ML"],
                "email": "xxx@xxx.com",
                "organization": "Stanford University",
                "confidence_score": 0.95
            }
        """
        try:
            # 步骤1: 搜索学者
            search_result = await self.search_scholar(name, affiliation, size=10)
            if not search_result or not search_result.get('data', {}).get('hits'):
                logger.warning(f"[AMiner] 未找到 {name} 的学者记录")
                return {
                    "is_verified": False,
                    "reason": "no_aminer_record"
                }
            
            hits = search_result['data']['hits']
            
            # 步骤2: 通过语义匹配找到最佳候选
            best_match = self._find_best_match(name, affiliation, hits, email)
            
            if best_match['confidence_score'] < 0.7:
                logger.warning(f"[AMiner] {name} 匹配度不足: {best_match['confidence_score']}")
                return {
                    "is_verified": False,
                    "reason": "low_confidence",
                    "confidence_score": best_match['confidence_score']
                }
            
            # 步骤3: 获取详细信息并补充interests
            person_detail = await self.get_person_detail(best_match['id'])
            
            # 提取关键字段
            enriched_data = {
                "is_verified": True,
                "aminer_id": best_match['id'],
                "name_cn": best_match.get('name_cn') or person_detail.get('name_cn'),
                "interests": best_match.get('interests', []),
                "email": best_match.get('email') or email,
                "organization": best_match.get('org'),
                "organization_cn": best_match.get('org_cn'),
                "confidence_score": best_match['confidence_score'],
                "education": best_match.get('education', []),
                "positions": best_match.get('positions', [])
            }
            
            logger.info(f"[AMiner] 验证成功: {name} - 置信度 {best_match['confidence_score']:.2f}")
            return enriched_data
            
        except Exception as e:
            logger.error(f"[AMiner] 验证和补充过程异常: {str(e)}")
            return {
                "is_verified": False,
                "reason": "validation_error",
                "error": str(e)
            }
    
    def _find_best_match(
        self,
        name: str,
        affiliation: str,
        hits: List[Dict],
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        通过多维度评分找到最佳匹配的学者
        
        评分维度：
        - 名字相似度
        - 机构匹配度
        - 邮箱匹配（如有）
        
        Args:
            name: 候选人英文姓名
            affiliation: 候选人机构
            hits: 搜索结果列表
            email: 候选人邮箱（可选）
            
        Returns:
            包含匹配信息和置信度的字典
        """
        best_hit = None
        best_score = 0.0
        
        name_lower = name.lower()
        affiliation_lower = affiliation.lower()
        
        for hit in hits:
            score = 0.0
            
            # 维度1: 名字匹配（权重0.4）
            hit_name = hit.get('name', '').lower()
            if hit_name == name_lower:
                score += 0.4  # 完全匹配
            elif name_lower.split()[-1] in hit_name.split():
                score += 0.3  # 姓氏匹配
            elif any(part in hit_name for part in name_lower.split()):
                score += 0.2  # 部分匹配
            
            # 维度2: 机构匹配（权重0.35）
            hit_org = hit.get('org', '').lower()
            if hit_org and affiliation_lower in hit_org or hit_org in affiliation_lower:
                score += 0.35  # 机构包含关系
            elif hit_org and len(hit_org) > 5:
                # 模糊匹配：检查关键词重叠
                affiliation_words = set(affiliation_lower.split())
                org_words = set(hit_org.split())
                overlap = len(affiliation_words & org_words) / max(len(affiliation_words), len(org_words))
                score += 0.35 * overlap
            
            # 维度3: 邮箱匹配（权重0.25，如果有）
            if email:
                hit_email = hit.get('email', '').lower()
                if hit_email == email.lower():
                    score += 0.25
                elif hit_email and email.split('@')[1] == hit_email.split('@')[1]:
                    score += 0.15  # 同域名
            
            if score > best_score:
                best_score = score
                best_hit = hit
        
        result = best_hit.copy() if best_hit else {"id": None}
        result['confidence_score'] = min(best_score, 1.0)  # 归一化到[0, 1]
        
        return result


# 创建全局API实例
aminer_api = AMinerAPI()

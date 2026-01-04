"""过滤节点 - 识别海外华人学者"""

from xpinyin import Pinyin
import logging

from app.agents.state import AgentState

logger = logging.getLogger(__name__)

# 初始化拼音转换器
pinyin = Pinyin()

# 表明是中国大陆的关键词（这些应该被跳过，因为不是"海外"）
MAINLAND_CHINA_KEYWORDS = [
    "tsinghua", "peking university", "pku", "beijing", "shanghai",
    "fudan", "zhejiang university", "nanjing", "china", "chinese academy",
    "cas", "ustc", "harbin", "wuhan", "xi'an", "chengdu", "guangzhou"
]


def is_chinese_name(name: str) -> bool:
    """
    使用拼音转换检查姓名是否为中文
    
    Args:
        name: 要检查的全名
        
    Returns:
        如果姓名看起来是中文则返回True
    """
    try:
        # 转换为拼音 - 如果已经是拼音/英文，不会有太大变化
        pinyin_result = pinyin.get_pinyin(name, '')
        
        # 简单启发式：如果姓名较短（2-4个字符）且包含汉字
        # 或者姓名包含常见的中文姓氏模式
        
        # 直接检查汉字
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in name)
        
        if has_chinese:
            return True
        
        # 常见的中文姓氏英文拼音
        common_surnames = [
            'wang', 'li', 'zhang', 'liu', 'chen', 'yang', 'huang', 'zhao',
            'wu', 'zhou', 'xu', 'sun', 'ma', 'zhu', 'hu', 'guo', 'he', 'gao',
            'lin', 'luo', 'zheng', 'liang', 'song', 'tang', 'xu', 'han', 'feng',
            'xie', 'yu', 'peng', 'cao'
        ]
        
        name_lower = name.lower()
        first_word = name_lower.split()[0] if name_lower.split() else ""
        
        return first_word in common_surnames
        
    except Exception as e:
        logger.warning(f"拼音检查失败 '{name}': {str(e)}")
        return False


def is_mainland_china(affiliation: str) -> bool:
    """
    检查所属单位是否在中国大陆
    
    Args:
        affiliation: 机构/所属单位字符串
        
    Returns:
        如果所属单位在中国大陆则返回True（应该被跳过）
    """
    aff_lower = affiliation.lower()
    return any(keyword in aff_lower for keyword in MAINLAND_CHINA_KEYWORDS)


def filter_node(state: AgentState) -> AgentState:
    """
    节点2: 过滤
    将候选人标记为SKIPPED，如果他们：
    1. 不是中文姓名，或
    2. 在中国大陆（不是"海外"）
    
    Args:
        state: 当前智能体状态
        
    Returns:
        应用过滤后的更新状态
    """
    logger.info("[过滤节点] 开始过滤流程")
    
    candidates = state["candidates"]
    
    for idx, candidate in enumerate(candidates):
        if candidate.status != "PENDING":
            continue
        
        # 检查1: 姓名是否为中文？
        name_is_chinese = is_chinese_name(candidate.name)
        
        # 检查2: 所属单位是否在中国大陆？
        is_mainland = is_mainland_china(candidate.affiliation)
        
        # 如果不是中文或在中国大陆则跳过
        if not name_is_chinese:
            candidate.status = "SKIPPED"
            candidate.skip_reason = "姓名看起来不是中文"
            logger.info(f"  [{idx}] 跳过: {candidate.name} - 不是中文姓名")
            
        elif is_mainland:
            candidate.status = "SKIPPED"
            candidate.skip_reason = "所属单位在中国大陆（非海外）"
            logger.info(f"  [{idx}] 跳过: {candidate.name} - 大陆单位")
        
        else:
            logger.info(f"  [{idx}] 通过: {candidate.name} ({candidate.affiliation})")
    
    # 统计结果
    pending_count = sum(1 for c in candidates if c.status == "PENDING")
    skipped_count = sum(1 for c in candidates if c.status == "SKIPPED")
    
    logger.info(f"[过滤节点] 完成: {pending_count}个待处理, {skipped_count}个已跳过")
    
    return state


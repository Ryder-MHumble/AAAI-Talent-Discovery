"""LangGraph工作流定义"""

from langgraph.graph import StateGraph, END
from typing import Literal
import logging

from app.agents.state import AgentState
from app.agents.nodes.ingestion import ingestion_node
from app.agents.nodes.filter import filter_node
from app.agents.nodes.detective import detective_node
from app.agents.nodes.auditor import auditor_node

logger = logging.getLogger(__name__)


def should_continue_processing(state: AgentState) -> Literal["detective", "complete"]:
    """
    路由函数，确定是否继续处理或完成
    
    Args:
        state: 当前智能体状态
        
    Returns:
        下一个节点名称或"complete"
    """
    candidates = state["candidates"]
    current_index = state["current_index"]
    
    # 检查是否还有待处理的PENDING候选人
    remaining = any(
        c.status == "PENDING" 
        for c in candidates[current_index:]
    )
    
    if remaining:
        logger.info(f"[路由器] 继续处理 (index={current_index})")
        return "detective"
    else:
        logger.info("[路由器] 所有候选人已处理完成")
        state["is_complete"] = True
        return "complete"


def create_agent_graph() -> StateGraph:
    """
    创建并返回智能体工作流图
    
    工作流:
    1. Ingestion -> 从AAAI加载候选人
    2. Filter -> 将非目标候选人标记为SKIPPED
    3. Detective -> 搜索主页（为每个候选人循环）
    4. Auditor -> 验证并提取信息
    5. Router -> 检查是否需要处理更多候选人
    
    Returns:
        已编译的StateGraph
    """
    # 初始化图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("ingestion", ingestion_node)
    workflow.add_node("filter", filter_node)
    workflow.add_node("detective", detective_node)
    workflow.add_node("auditor", auditor_node)
    
    # 定义边
    workflow.set_entry_point("ingestion")
    
    # Ingestion -> Filter
    workflow.add_edge("ingestion", "filter")
    
    # Filter -> Detective (开始处理)
    workflow.add_edge("filter", "detective")
    
    # Detective -> Auditor (找到URL后)
    workflow.add_edge("detective", "auditor")
    
    # Auditor -> Router (检查是否需要处理更多)
    workflow.add_conditional_edges(
        "auditor",
        should_continue_processing,
        {
            "detective": "detective",  # 循环回去处理下一个候选人
            "complete": END
        }
    )
    
    # 编译图
    app = workflow.compile()
    
    logger.info("[图] 智能体工作流编译成功")
    
    return app


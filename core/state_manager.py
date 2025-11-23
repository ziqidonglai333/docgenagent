"""
状态管理器 - 定义和管理LangGraph工作流状态
"""

from typing import Dict, List, Any, Optional, TypedDict
from dataclasses import dataclass, field
import json


class ReportState(TypedDict):
    """报告生成工作流状态定义"""
    # 基础信息
    topic: str
    keywords: List[str]
    current_step: str
    
    # 搜索数据
    search_results: List[Dict[str, Any]]
    raw_content: Dict[str, str]
    
    # 目录信息
    outline: List[str]
    outline_approved: bool
    
    # 章节内容
    chapter_contents: Dict[str, Dict[str, Any]]
    chapter_approvals: Dict[str, bool]
    
    # 图表数据
    charts: Dict[str, Dict[str, Any]]
    
    # 报告生成
    final_report: Optional[str]
    word_file_path: Optional[str]
    
    # 用户交互
    user_feedback: Dict[str, str]
    current_chapter: str


@dataclass
class WorkflowState:
    """工作流状态数据类"""
    topic: str = ""
    keywords: List[str] = field(default_factory=list)
    current_step: str = "initial"
    
    # 搜索相关
    search_results: List[Dict[str, Any]] = field(default_factory=list)
    raw_content: Dict[str, str] = field(default_factory=dict)
    
    # 目录相关
    outline: List[str] = field(default_factory=list)
    outline_approved: bool = False
    
    # 章节相关
    chapter_contents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    chapter_approvals: Dict[str, bool] = field(default_factory=dict)
    
    # 图表相关
    charts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # 报告相关
    final_report: Optional[str] = None
    word_file_path: Optional[str] = None
    
    # 用户交互
    user_feedback: Dict[str, str] = field(default_factory=dict)
    current_chapter: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "topic": self.topic,
            "keywords": self.keywords,
            "current_step": self.current_step,
            "search_results": self.search_results,
            "raw_content": self.raw_content,
            "outline": self.outline,
            "outline_approved": self.outline_approved,
            "chapter_contents": self.chapter_contents,
            "chapter_approvals": self.chapter_approvals,
            "charts": self.charts,
            "final_report": self.final_report,
            "word_file_path": self.word_file_path,
            "user_feedback": self.user_feedback,
            "current_chapter": self.current_chapter
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowState':
        """从字典创建实例"""
        state = cls()
        for key, value in data.items():
            if hasattr(state, key):
                setattr(state, key, value)
        return state
    
    def save_to_file(self, filepath: str) -> None:
        """保存状态到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'WorkflowState':
        """从文件加载状态"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def get_progress(self) -> float:
        """获取工作流进度百分比"""
        steps = {
            "initial": 0,
            "searching": 10,
            "outline_generated": 30,
            "outline_approved": 40,
            "content_generating": 50,
            "content_approved": 80,
            "compiling": 90,
            "completed": 100
        }
        return steps.get(self.current_step, 0)
    
    def is_chapter_approved(self, chapter: str) -> bool:
        """检查章节是否已批准"""
        return self.chapter_approvals.get(chapter, False)
    
    def all_chapters_approved(self) -> bool:
        """检查所有章节是否都已批准"""
        if not self.outline:
            return False
        return all(self.is_chapter_approved(chapter) for chapter in self.outline)
    
    def get_next_chapter(self) -> Optional[str]:
        """获取下一个待处理的章节"""
        for chapter in self.outline:
            if not self.is_chapter_approved(chapter):
                return chapter
        return None


class StateManager:
    """状态管理器"""
    
    def __init__(self):
        self.current_state = WorkflowState()
    
    def update_step(self, step: str) -> None:
        """更新当前步骤"""
        self.current_state.current_step = step
    
    def add_search_result(self, result: Dict[str, Any]) -> None:
        """添加搜索结果"""
        self.current_state.search_results.append(result)
    
    def set_outline(self, outline: List[str]) -> None:
        """设置目录"""
        self.current_state.outline = outline
        # 初始化章节批准状态
        for chapter in outline:
            if chapter not in self.current_state.chapter_approvals:
                self.current_state.chapter_approvals[chapter] = False
    
    def approve_outline(self) -> None:
        """批准目录"""
        self.current_state.outline_approved = True
        self.update_step("outline_approved")
    
    def update_chapter_content(self, chapter: str, content: Dict[str, Any]) -> None:
        """更新章节内容"""
        self.current_state.chapter_contents[chapter] = content
        self.current_state.current_chapter = chapter
    
    def approve_chapter(self, chapter: str) -> None:
        """批准章节"""
        self.current_state.chapter_approvals[chapter] = True
    
    def add_chart(self, chart_id: str, chart_data: Dict[str, Any]) -> None:
        """添加图表"""
        self.current_state.charts[chart_id] = chart_data
    
    def set_final_report(self, report_content: str, file_path: str) -> None:
        """设置最终报告"""
        self.current_state.final_report = report_content
        self.current_state.word_file_path = file_path
        self.update_step("completed")
    
    def reset(self) -> None:
        """重置状态"""
        self.current_state = WorkflowState()

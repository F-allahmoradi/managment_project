"""ثبت ابزارهای CRUD روی سرور MCP.

mcp_server/server.py این تابع را صدا می‌زند.
محتوا زیرساخت مشترک است. جلسه سرور جدا است.
ارسال تلگرام مال reminder است.
"""

from logging_module import setup_logging
from mcp.server.mcpserver import MCPServer
from mcp_server.tools.permission.create_permission import (
    register as register_create_permission,
)
from mcp_server.tools.permission.list_permissions import (
    register as register_list_permissions,
)
from mcp_server.tools.project.create_project import (
    register as register_create_project,
)
from mcp_server.tools.project.delete_project import (
    register as register_delete_project,
)
from mcp_server.tools.project.get_project import register as register_get_project
from mcp_server.tools.project.list_projects import (
    register as register_list_projects,
)
from mcp_server.tools.project.update_project import (
    register as register_update_project,
)
from mcp_server.tools.project_member.create_project_member import (
    register as register_create_project_member,
)
from mcp_server.tools.project_member.list_project_members import (
    register as register_list_project_members,
)
from mcp_server.tools.project_member.update_project_member import (
    register as register_update_project_member,
)
from mcp_server.tools.task.create_task import register as register_create_task
from mcp_server.tools.task.delete_task import register as register_delete_task
from mcp_server.tools.task.get_task import register as register_get_task
from mcp_server.tools.task.list_tasks import register as register_list_tasks
from mcp_server.tools.task.update_task import register as register_update_task
from mcp_server.tools.task_item.complete_task_item import (
    register as register_complete_task_item,
)
from mcp_server.tools.task_item.create_task_item import (
    register as register_create_task_item,
)
from mcp_server.tools.task_item.delete_task_item import (
    register as register_delete_task_item,
)
from mcp_server.tools.task_item.list_task_items import (
    register as register_list_task_items,
)
from mcp_server.tools.task_item.update_task_item import (
    register as register_update_task_item,
)
from mcp_server.tools.task_follow_up.create_task_follow_up import (
    register as register_create_task_follow_up,
)
from mcp_server.tools.task_follow_up.get_task_follow_up import (
    register as register_get_task_follow_up,
)
from mcp_server.tools.task_follow_up.list_task_follow_ups import (
    register as register_list_task_follow_ups,
)
from mcp_server.tools.external_contact.create_external_contact import (
    register as register_create_external_contact,
)
from mcp_server.tools.external_contact.get_external_contact import (
    register as register_get_external_contact,
)
from mcp_server.tools.external_contact.list_external_contacts import (
    register as register_list_external_contacts,
)
from mcp_server.tools.chat.create_chat import register as register_create_chat
from mcp_server.tools.chat.get_chat import register as register_get_chat
from mcp_server.tools.chat.list_chats import register as register_list_chats
from mcp_server.tools.chat_member.create_chat_member import (
    register as register_create_chat_member,
)
from mcp_server.tools.chat_member.list_chat_members import (
    register as register_list_chat_members,
)
from mcp_server.tools.message.create_message import (
    register as register_create_message,
)
from mcp_server.tools.message.get_message import register as register_get_message
from mcp_server.tools.message.list_messages import (
    register as register_list_messages,
)
from mcp_server.tools.message_recipient.create_message_recipient import (
    register as register_create_message_recipient,
)
from mcp_server.tools.message_recipient.list_message_recipients import (
    register as register_list_message_recipients,
)
from mcp_server.tools.notification.get_notification import (
    register as register_get_notification,
)
from mcp_server.tools.notification.list_notifications import (
    register as register_list_notifications,
)
from mcp_server.tools.notification.mark_notification_read import (
    register as register_mark_notification_read,
)
from mcp_server.tools.audit_log.get_audit_log import (
    register as register_get_audit_log,
)
from mcp_server.tools.audit_log.list_audit_logs import (
    register as register_list_audit_logs,
)
from mcp_server.tools.performance_action.create_performance_action import (
    register as register_create_performance_action,
)
from mcp_server.tools.performance_action.get_performance_action import (
    register as register_get_performance_action,
)
from mcp_server.tools.performance_action.list_performance_actions import (
    register as register_list_performance_actions,
)
from mcp_server.tools.content.create_content import (
    register as register_create_content,
)
from mcp_server.tools.content.delete_content import (
    register as register_delete_content,
)
from mcp_server.tools.content.get_content import register as register_get_content
from mcp_server.tools.content.list_contents import (
    register as register_list_contents,
)
from mcp_server.tools.text_analysis.save_text_analysis import (
    register as register_save_text_analysis,
)
from mcp_server.tools.text_analysis.get_text_analysis import (
    register as register_get_text_analysis,
)
from mcp_server.tools.text_analysis.list_text_analyses import (
    register as register_list_text_analyses,
)
from mcp_server.tools.issue.create_issue import register as register_create_issue
from mcp_server.tools.issue.get_issue import register as register_get_issue
from mcp_server.tools.issue.list_issues import register as register_list_issues
from mcp_server.tools.issue.link_issue_cause import register as register_link_issue_cause
from mcp_server.tools.issue.link_issue_task import register as register_link_issue_task
from mcp_server.tools.issue.set_issue_importance import (
    register as register_set_issue_importance,
)
from mcp_server.tools.issue.set_issue_urgency import (
    register as register_set_issue_urgency,
)
from mcp_server.tools.issue.set_issue_severity import (
    register as register_set_issue_severity,
)
from mcp_server.tools.issue.add_issue_impact import register as register_add_issue_impact
from mcp_server.tools.issue.link_issue_topic import register as register_link_issue_topic
from mcp_server.tools.issue.link_issue_entity import (
    register as register_link_issue_entity,
)
from mcp_server.tools.role.create_role import register as register_create_role
from mcp_server.tools.role.delete_role import register as register_delete_role
from mcp_server.tools.role.get_role import register as register_get_role
from mcp_server.tools.role.list_roles import register as register_list_roles
from mcp_server.tools.role.update_role import register as register_update_role
from mcp_server.tools.role_permission.create_role_permission import (
    register as register_create_role_permission,
)
from mcp_server.tools.role_permission.delete_role_permission import (
    register as register_delete_role_permission,
)
from mcp_server.tools.role_permission.list_role_permissions import (
    register as register_list_role_permissions,
)
from mcp_server.tools.user.create_user import register as register_create_user
from mcp_server.tools.user.delete_user import register as register_delete_user
from mcp_server.tools.user.get_user import register as register_get_user
from mcp_server.tools.user.list_assignable_users import (
    register as register_list_assignable_users,
)
from mcp_server.tools.user.list_users import register as register_list_users
from mcp_server.tools.user.update_user import register as register_update_user
from mcp_server.tools.user_role.create_user_role import (
    register as register_create_user_role,
)
from mcp_server.tools.user_role.delete_user_role import (
    register as register_delete_user_role,
)
from mcp_server.tools.user_role.list_user_roles import (
    register as register_list_user_roles,
)


def register_crud_tools(mcp: MCPServer) -> None:
    """ابزارهای CRUD را روی سرور ثبت می‌کند.

    ورودی:
        mcp: نمونه FastMCP/MCPServer همین پروژه.
    خروجی:
        هیچ. اثر جانبی ثبت tool است.
    فراخوانی‌ها:
        setup_logging و register ابزارهای User و Role و Permission
        و پروژه و اعضا و وظیفه و پیگیری و گزارش و ایده/تجربه
        و مخاطب خارجی و گفتگو و پیام و اعلان داخل پنل و ممیزی
        و تشویق و تنبیه و محتوا و تحلیل متن و مسئله و علت مسئله و وظیفه مسئله
        و امتیاز مسئله و موضوع و موجودیت مسئله و زیرکار.
    علت:
        جلسه روی سرور جدا است. ارسال تلگرام مال reminder است.
    """
    setup_logging()
    register_create_user(mcp)
    register_get_user(mcp)
    register_list_users(mcp)
    register_list_assignable_users(mcp)
    register_update_user(mcp)
    register_delete_user(mcp)
    register_create_role(mcp)
    register_get_role(mcp)
    register_list_roles(mcp)
    register_update_role(mcp)
    register_delete_role(mcp)
    register_create_permission(mcp)
    register_list_permissions(mcp)
    register_create_role_permission(mcp)
    register_list_role_permissions(mcp)
    register_delete_role_permission(mcp)
    register_create_user_role(mcp)
    register_list_user_roles(mcp)
    register_delete_user_role(mcp)
    register_create_project(mcp)
    register_get_project(mcp)
    register_list_projects(mcp)
    register_update_project(mcp)
    register_delete_project(mcp)
    register_create_project_member(mcp)
    register_list_project_members(mcp)
    register_update_project_member(mcp)
    register_create_task(mcp)
    register_get_task(mcp)
    register_list_tasks(mcp)
    register_update_task(mcp)
    register_delete_task(mcp)
    register_create_task_item(mcp)
    register_list_task_items(mcp)
    register_update_task_item(mcp)
    register_complete_task_item(mcp)
    register_delete_task_item(mcp)
    register_create_task_follow_up(mcp)
    register_get_task_follow_up(mcp)
    register_list_task_follow_ups(mcp)
    register_create_external_contact(mcp)
    register_get_external_contact(mcp)
    register_list_external_contacts(mcp)
    register_create_chat(mcp)
    register_get_chat(mcp)
    register_list_chats(mcp)
    register_create_chat_member(mcp)
    register_list_chat_members(mcp)
    register_create_message(mcp)
    register_get_message(mcp)
    register_list_messages(mcp)
    register_create_message_recipient(mcp)
    register_list_message_recipients(mcp)
    register_list_notifications(mcp)
    register_get_notification(mcp)
    register_mark_notification_read(mcp)
    register_list_audit_logs(mcp)
    register_get_audit_log(mcp)
    register_create_performance_action(mcp)
    register_get_performance_action(mcp)
    register_list_performance_actions(mcp)
    register_create_content(mcp)
    register_get_content(mcp)
    register_list_contents(mcp)
    register_delete_content(mcp)
    register_save_text_analysis(mcp)
    register_get_text_analysis(mcp)
    register_list_text_analyses(mcp)
    register_create_issue(mcp)
    register_get_issue(mcp)
    register_list_issues(mcp)
    register_link_issue_cause(mcp)
    register_link_issue_task(mcp)
    register_set_issue_importance(mcp)
    register_set_issue_urgency(mcp)
    register_set_issue_severity(mcp)
    register_add_issue_impact(mcp)
    register_link_issue_topic(mcp)
    register_link_issue_entity(mcp)

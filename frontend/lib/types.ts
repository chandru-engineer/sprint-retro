export type UserRole = "admin" | "pmo" | "member";

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TeamMember {
  id: number;
  name: string;
  email: string;
}

export interface Team {
  id: number;
  name: string;
  description: string;
  team_lead_id: number | null;
  is_active: boolean;
  created_at: string;
  members: TeamMember[];
}

export interface OrgOption {
  id: number;
  name: string;
  role: UserRole;
}

export type ProjectStatus = "active" | "inactive";

export interface Project {
  id: number;
  name: string;
  description: string;
  team_id: number;
  status: ProjectStatus;
  created_at: string;
}

export type RetroStatus = "draft" | "open" | "completed";
export type InvitationStatus = "pending" | "sent" | "failed";
export type FeedbackStatus = "not_started" | "draft" | "submitted";

export interface Retro {
  id: number;
  project_id: number;
  team_id: number;
  name: string;
  sprint_name: string;
  sprint_start_date: string;
  sprint_end_date: string;
  retro_date: string;
  retro_time: string;
  status: RetroStatus;
  created_by: number;
  created_at: string;
}

export interface RetroSummary extends Retro {
  project_name: string;
  team_name: string;
  submitted_count: number;
  total_count: number;
  completion_percent: number;
}

export interface Participant {
  id: number;
  user_id: number;
  user_name: string;
  user_email: string;
  invitation_status: InvitationStatus;
  feedback_status: FeedbackStatus;
  invited_at: string | null;
  submitted_at: string | null;
}

export interface RetroDetail extends Retro {
  participants: Participant[];
  submitted_count: number;
  total_count: number;
  completion_percent: number;
}

export interface FeedbackForm {
  achievement: string;
  went_well: string;
  did_not_go_well: string;
  learnings: string;
  improvements: string;
}

export interface Feedback extends FeedbackForm {
  id: number;
  retro_id: number;
  user_id: number;
  status: FeedbackStatus;
  created_at: string;
  updated_at: string;
  submitted_at: string | null;
}

export interface ReactionSummary {
  emoji: string;
  count: number;
  reacted_by_me: boolean;
}

export interface FeedbackWithUser extends Feedback {
  user_name: string;
  reactions: Record<string, ReactionSummary[]>;
}

export interface Report {
  project_name: string;
  team_name: string;
  sprint_name: string;
  sprint_start_date: string;
  sprint_end_date: string;
  retro_date: string;
  retro_time: string;
  participants: number;
  responses: number;
  achievements: string[];
  went_well: string[];
  did_not_go_well: string[];
  learnings: string[];
  improvements: string[];
}

export interface HeroCandidate {
  id: number;
  name: string;
  email: string;
}

export interface HeroVote {
  candidate_id: number;
  candidate_name: string;
  is_anonymous: boolean;
  comment: string | null;
  updated_at: string;
}

export interface HeroVoteEntry {
  voter_name: string | null;
  comment: string | null;
}

export interface HeroVoteResultItem {
  user_id: number;
  user_name: string;
  vote_count: number;
  entries: HeroVoteEntry[];
}

export interface HeroVoteResults {
  retro_id: number;
  total_votes: number;
  results: HeroVoteResultItem[];
}

export interface CredIssuerTemplate {
  id: string;
  name: string;
  description: string;
}

export interface CredIssuerConfig {
  configured: boolean;
  template_id: string | null;
  template_name: string | null;
  api_key_masked: string | null;
  updated_at: string | null;
}

export interface IssuedCredential {
  id: number;
  user_id: number;
  user_name: string;
  template_name: string;
  vc_id: string;
  status: string;
  issued_at: string;
}

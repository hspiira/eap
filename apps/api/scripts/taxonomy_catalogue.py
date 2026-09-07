"""The service catalogue and diagnosis taxonomy, with sourced descriptions.

Usage: uv run python scripts/taxonomy_catalogue.py

Writes the three import payloads under ``data/taxonomy/``. This module is the
source of record for the catalogue: it holds no spreadsheet dependency, and a
re-run reproduces the files exactly.

Descriptions follow employee assistance and workplace wellness standards.
Every external claim in a description names its source inline. The full
reference list is in docs/TAXONOMY_CATALOGUE.md.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "data/taxonomy"

# (name, ServiceCategory or None, is_group_service, description)
SERVICES: list[tuple[str, str | None, bool, str]] = [
    (
        "Individual Counselling",
        "ShortTermCounselling",
        False,
        "Confidential one-to-one counselling for an employee or a covered dependant, "
        "delivered as a bounded course of sessions rather than open-ended therapy. "
        "This is the employee assistance core technology in its narrowest form: timely, "
        "confidential problem identification and assessment, followed by short-term "
        "intervention, and referral out when the presenting problem needs longer or "
        "specialist care (EAPA Core Technology, items 3 to 5). No professional standard "
        "fixes the number of sessions; EASNA describes brief EAP counselling as roughly "
        "one to six sessions set by programme philosophy and funding, so the entitlement "
        "belongs in the client contract, not in this catalogue. Each session records the "
        "presenting problem, the diagnosis type and diagnosis where one is established, "
        "and the disposition: to be continued, referred, or completed.",
    ),
    (
        "Couple Counselling",
        "ShortTermCounselling",
        False,
        "Short-term counselling with two partners seen together, where the relationship "
        "itself is the presenting problem rather than one partner's individual condition. "
        "Used for conflict, separation and divorce, infidelity, and the breakdown of trust, "
        "and commonly opened when an employee's individual sessions establish that the "
        "distress is relational in origin. Both partners are clients of the session even "
        "when only one is the covered employee, which affects consent and note-keeping: "
        "each partner's disclosures are held to the same confidentiality as any other "
        "client. Referred on where there is intimate partner violence, since couple work "
        "is contraindicated while a partner is unsafe.",
    ),
    (
        "Family Therapy",
        "ShortTermCounselling",
        True,
        "Counselling with a family group, addressing the family system rather than one "
        "member in isolation. Typical use is parenting and child behaviour, "
        "intergenerational conflict, caregiving strain, adjustment after a death or a "
        "separation, and supporting a family through one member's mental or physical "
        "illness. WHO identifies family interventions as part of recommended care for "
        "severe conditions including schizophrenia and bipolar disorder, so this service "
        "carries part of the follow-up for referred cases as well as standalone work. "
        "Attendance varies between sessions, so the session record names who attended "
        "rather than assuming a fixed group.",
    ),
    (
        "Group Counselling",
        "ShortTermCounselling",
        True,
        "Facilitated therapeutic group work with employees who do not otherwise form a "
        "family or couple, convened around a shared presenting problem such as loss, "
        "substance recovery, or workplace change. Distinct from a health talk: the "
        "purpose is therapeutic process among members, not information delivery, so "
        "membership is screened, the group is closed for its duration, and "
        "confidentiality obligations run between members as well as to the facilitator. "
        "WHO conditionally recommends stress management delivered on mindfulness or "
        "cognitive behavioural lines as a workplace intervention, which is the evidence "
        "base most of these groups draw on.",
    ),
    (
        "Trauma Group Counselling",
        None,
        True,
        "Group work with employees exposed to the same traumatic event, such as a "
        "robbery, a fatal accident, or a violent incident at a work site. This service "
        "must not be delivered as single-session psychological debriefing: the WHO "
        "guidelines on mental health at work carry a strong recommendation against "
        "psychological debriefing to reduce the risk of post-traumatic stress, anxiety "
        "or depressive symptoms after a traumatic event. What is supported is screening, "
        "practical and social support, and referral of those who develop symptoms into "
        "trauma-focused therapy, which WHO recommends as trauma-focused cognitive "
        "behavioural therapy or EMDR. Its programme category is unresolved pending a "
        "decision on whether incident response is a separate entitlement.",
    ),
    (
        "Psychotherapy",
        "ShortTermCounselling",
        False,
        "Formal, modality-specific psychological treatment delivered over a longer course "
        "than brief EAP counselling, for example cognitive behavioural therapy or "
        "trauma-focused therapy. It sits at the edge of employee assistance scope: the "
        "core technology treats diagnosis and treatment as something the programme refers "
        "to and then monitors, rather than something it delivers itself (EAPA Core "
        "Technology, item 5). Recorded here because the programme sometimes contracts it "
        "directly for a member whose condition needs it and who has no other route to "
        "care. Sessions under this service should carry an established diagnosis, not a "
        "presenting concern alone.",
    ),
    (
        "Psychiatric Assessment",
        None,
        False,
        "Diagnostic assessment by a psychiatrist or other prescribing clinician, arranged "
        "for a member whose presentation needs medical evaluation, medication review, or "
        "confirmation of a diagnosis the counsellor cannot establish. This is a referral "
        "under EAPA Core Technology item 5, and the programme retains case monitoring and "
        "follow-up afterwards rather than closing the case at the point of referral. "
        "Typical triggers are psychosis, suspected bipolar disorder, suicidal risk, and a "
        "substance dependence needing withdrawal management. No programme category in the "
        "current schema describes assessment, so entitlement drawdown does not apply to "
        "it.",
    ),
    (
        "Individual Assessment",
        None,
        False,
        "A structured single-session evaluation of one member, producing a formulation and "
        "a plan rather than treatment. Distinguished from the first counselling session by "
        "intent: the deliverable is the assessment itself, most often for career "
        "direction, fitness for a role, or a psychometric or ADHD screen requested by the "
        "member or the employer. EAPA Core Technology item 3 makes confidential problem "
        "identification and assessment a defining EAP function, and item 8 requires that "
        "its effect on the organisation be evaluated, so the output is written and "
        "retained. Where an employer requests it, what is disclosed back to the employer "
        "is governed by consent given before the session.",
    ),
    (
        "Group Assessment",
        None,
        True,
        "Assessment applied across a team or cohort rather than one member, used to "
        "establish the psychosocial risk profile of a work unit before choosing an "
        "intervention. WHO lists the workplace risks to look for, among them excessive "
        "workload, low control over job design, unsocial or inflexible hours, weak "
        "colleague support, bullying and harassment, discrimination, unclear "
        "responsibilities, and job insecurity. Output is an aggregate finding for the "
        "employer, so individual responses are not attributable: small cell counts are "
        "suppressed and no member is identified. This is the diagnostic step before an "
        "organisational intervention, which WHO conditionally recommends for reducing "
        "distress.",
    ),
    (
        "Health Talk",
        None,
        True,
        "A psychoeducational session delivered to a group of employees on a health or "
        "wellbeing topic, without individual clinical contact. Its purpose is mental "
        "health literacy: WHO conditionally recommends training workers in mental health "
        "awareness to improve knowledge and reduce stigma, while noting the evidence that "
        "it changes help-seeking behaviour is not established. Also serves the core "
        "technology's promotion function, since a talk is the main way employees learn the "
        "programme exists and how to reach it (EAPA Core Technology, item 2). Attendance "
        "and topic are recorded; no diagnosis is attached, because nobody is assessed in "
        "a talk.",
    ),
    (
        "Mental Health Talk",
        None,
        True,
        "A health talk whose topic is mental health specifically: recognising depression "
        "and anxiety, managing stress, suicide awareness, and how to refer a colleague. "
        "Kept separate from the general health talk because it is the delivery vehicle for "
        "the mental health literacy WHO conditionally recommends, and because it needs a "
        "facilitator competent to handle disclosure in the room. Sessions frequently "
        "generate individual referrals afterwards, which are recorded as their own "
        "counselling sessions rather than against the talk. Content should name the "
        "programme's access route, since awareness without a route produces no help-seeking.",
    ),
    (
        "Medical Health Talk",
        None,
        True,
        "A health talk on physical health and disease management rather than mental health: "
        "hypertension, diabetes, HIV, cancer screening, nutrition, and adherence to "
        "treatment. Belongs in an employee assistance catalogue because physical illness is "
        "one of the most common routes into the programme, both for the employee managing "
        "their own diagnosis and for the employee caring for an ill relative. Pairs with the "
        "medical disease management diagnosis type, where the presenting concern is the "
        "psychological load of a physical condition. Delivered with or by clinical staff, "
        "and no individual health information is recorded from a talk.",
    ),
    (
        "Change Management Talk",
        None,
        True,
        "A group session for employees going through an organisational change: "
        "restructuring, redundancy, merger, relocation, or a new operating model. WHO lists "
        "job insecurity and inadequate investment in career development among the "
        "psychosocial risks at work, which is what makes announced change a predictable "
        "spike in demand on the programme. The session covers what is known, what is not, "
        "the normal course of adjustment, and how to reach individual support. It is not a "
        "substitute for the organisational change itself: WHO's strong recommendation is "
        "that reasonable accommodations be made for workers with mental health conditions, "
        "and a talk does not deliver that.",
    ),
    (
        "Empowerment Talk",
        None,
        True,
        "A group session aimed at personal agency and coping capability rather than at a "
        "clinical topic: assertiveness, boundary setting, financial literacy, "
        "decision-making, and confidence at work. Often commissioned for a specific "
        "cohort, for example women in a workforce, first-line supervisors, or young "
        "employees. Sits closest to WHO's conditional recommendation on universal "
        "psychosocial interventions, where stress management built on mindfulness or "
        "cognitive behavioural approaches may be considered for mental health promotion. "
        "No diagnosis attaches, and the record is topic, audience and attendance.",
    ),
    (
        "Training",
        None,
        True,
        "Structured skills training rather than an awareness talk, most importantly manager "
        "and supervisor training. This is the strongest evidence-backed service in the "
        "catalogue: WHO makes a strong recommendation, on moderate-certainty evidence, that "
        "managers be trained to support their workers' mental health, to improve managers' "
        "knowledge, attitudes and behaviours and workers' help-seeking. It is also the first "
        "item of the EAPA Core Technology, which names consultation with and training of "
        "work organisation leadership as a defining EAP function. Content covers "
        "recognising distress, holding a supportive conversation, the referral route, and "
        "the limits of a manager's role. Delivered to a roster with an attendance record, "
        "since the employer is the client for this service.",
    ),
    (
        "Coaching/Mentorship",
        "WellnessCoaching",
        False,
        "Goal-directed one-to-one work on performance, career direction, leadership "
        "capability, or a specific transition, where the member is not presenting a "
        "clinical problem. Distinguished from counselling by contract and direction: the "
        "agenda is forward-looking and set by the member's goal, and the practitioner is "
        "not treating a condition. Kept in the catalogue and out of the diagnosis taxonomy "
        "deliberately, because coaching is an intervention and recording it as a diagnosis "
        "would inflate clinical prevalence with sessions that had no clinical finding. "
        "Where coaching surfaces a clinical problem, the case is converted to counselling "
        "or referred, and that is recorded as a separate session.",
    ),
    (
        "Physical Wellness",
        "WellnessCoaching",
        False,
        "Structured physical activity and fitness support offered as a mental health "
        "intervention, individually or in a group: exercise sessions, activity challenges, "
        "and fitness guidance. WHO conditionally recommends that opportunities for "
        "leisure-based physical activity be considered to improve mental health and work "
        "ability, on very low-certainty evidence, so the service is worth offering and worth "
        "describing honestly as promotion rather than treatment. Belongs to health promotion "
        "in the taxonomy and should not carry a clinical diagnosis. Participation is the "
        "unit recorded; the activity itself belongs in the session's topic field, not in the "
        "diagnosis.",
    ),
    (
        "Site Visit",
        None,
        False,
        "A programme visit to an employer's premises to deliver services on site, whether "
        "counselling, a talk, or a check-in with a work unit after an incident. Recorded as "
        "its own service because the visit is what the employer commissions and is billed "
        "for, and because presence on site changes what the practitioner can offer: less "
        "privacy, more informal contact, and higher chance of unplanned disclosure. Where a "
        "visit produces individual clinical contact, that contact should also be recorded "
        "as the counselling service it was, so clinical volume is not hidden inside a "
        "logistics line. This is a delivery arrangement rather than a clinical "
        "intervention, and it carries no programme category.",
    ),
    (
        "Hospital Visit",
        None,
        False,
        "A visit to a member who is admitted to hospital, or attendance at a clinical "
        "case conference about them. Serves the case monitoring and follow-up duty in EAPA "
        "Core Technology item 5, which is what keeps a referred member from disappearing "
        "into the health system with the programme unaware of the outcome. Also used to "
        "coordinate with treating clinicians and to support the family at the bedside. "
        "Consent to be visited and to liaise with the treating team is obtained before the "
        "visit, and what is shared back to the employer is limited to fitness and "
        "availability, never diagnosis.",
    ),
    (
        "Home Visit",
        None,
        False,
        "A visit to a member's home, used when the member cannot travel, has withdrawn from "
        "contact, or is being supported through bereavement, serious illness, or "
        "post-crisis recovery. The highest-risk delivery arrangement in the catalogue: it "
        "removes the clinical setting, brings the practitioner into a family system, and "
        "raises real safety questions where the presenting problem is domestic abuse. It "
        "should be authorised case by case rather than offered as a standing option, with a "
        "lone-working precaution recorded. As with the other visit services, this describes "
        "where the session happened; the clinical work itself is recorded under the "
        "counselling service delivered.",
    ),
]

# (code, name, description)
DIAGNOSIS_TYPES: list[tuple[str, str, str]] = [
    (
        "MENTAL_ILL_HEALTH",
        "Mental Ill Health",
        "Diagnosable mental disorders presenting to the programme, as distinct from the "
        "distress and life problems that make up most of the rest of this taxonomy. Maps "
        "onto the ICD-11 chapter on mental, behavioural and neurodevelopmental disorders, "
        "drawing mainly on its mood disorders and primary psychotic disorders groupings. "
        "WHO estimates 15% of working-age adults had a mental disorder in 2019, and that "
        "12 billion working days are lost each year to depression and anxiety at about "
        "US$1 trillion in lost productivity, which is the case for the programme existing "
        "at all. A leaf under this type usually means a referral: the core technology "
        "treats diagnosis and treatment as something the EAP refers to and then monitors.",
    ),
    (
        "FAMILY_RELATIONSHIP",
        "Family & Relationship",
        "Distress arising from the member's intimate, marital and family relationships, "
        "including conflict, separation, infidelity, abuse within the relationship, and "
        "the strain of caregiving. Consistently the largest presenting category in "
        "workplace programmes, and it is not a clinical grouping: these are life problems "
        "that affect job performance, which is precisely the scope the employee assistance "
        "core technology defines. The type is used both for work with the couple or family "
        "and for individual sessions where the relationship is the subject. Where the "
        "presenting problem is violence or coercion rather than conflict, it belongs under "
        "gender-based violence, because conflating the two hides the safety risk.",
    ),
    (
        "WORK_STRESS_ANXIETY",
        "Work Stress / Anxiety",
        "Distress whose origin is the work itself: workload, hours, conflict with "
        "colleagues or managers, toxic team dynamics, appraisal pressure, and the "
        "exhaustion that follows. WHO calls these psychosocial risks and lists them "
        "explicitly, including excessive workload, limited control over job design, "
        "unsocial or inflexible schedules, weak colleague support, bullying, and unclear "
        "responsibilities. This is the type that should drive organisational feedback "
        "rather than only individual counselling: WHO conditionally recommends "
        "organisational interventions that reduce or remove the risk factor, and strongly "
        "recommends reasonable accommodations for workers with mental health conditions. "
        "A high count here is a finding about the employer, not only about its employees.",
    ),
    (
        "CAREER_CHALLENGES",
        "Career Challenges",
        "Concerns about the shape and direction of the member's working life: stagnation, "
        "demotion, promotion readiness, role fit, and fatigue with the career rather than "
        "with the current workload. WHO lists under-use of skills, under- or "
        "over-promotion, and inadequate investment in career development among workplace "
        "psychosocial risks, which is why career work belongs in a wellness programme and "
        "not only in HR. Sessions here are typically coaching in character rather than "
        "clinical, and carry no mental disorder. Kept separate from work stress so that a "
        "member wanting career direction is not counted as a distressed employee.",
    ),
    (
        "TRAUMA",
        "Trauma",
        "Presentations following exposure to a threatening or horrific event, whether a "
        "single incident or sustained exposure. ICD-11 places post-traumatic stress "
        "disorder at 6B40 and introduced complex post-traumatic stress disorder at 6B41 "
        "for repeated and prolonged trauma, commonly of childhood origin, adding "
        "disturbances of affect regulation, self-concept and relationships to the core "
        "PTSD features. WHO recommends trauma-focused cognitive behavioural therapy or "
        "EMDR for adults with PTSD, and recommends strongly against single-session "
        "psychological debriefing after a traumatic event. Not every trauma exposure "
        "produces a disorder, so this type covers both the diagnosable condition and "
        "post-incident support that resolves without one.",
    ),
    (
        "LOSS_GRIEF",
        "Loss & Grief",
        "Bereavement and other significant loss, including death of a relative, "
        "disappearance of a family member, and loss of property or livelihood. Grief is a "
        "normal response and most of it needs support rather than treatment, which is why "
        "this type sits outside the mental ill health grouping. ICD-11 does recognise a "
        "boundary case: prolonged grief disorder at 6B42, marked by persistent longing "
        "for and preoccupation with the deceased with significant functional impairment "
        "continuing well beyond the loss, conventionally at least six months. The "
        "practical distinction for a counsellor is duration and impairment, not intensity, "
        "and a persistent case is a referral rather than an extended course of counselling.",
    ),
    (
        "ADDICTIONS",
        "Addictions",
        "Substance use and addictive behaviour, covering alcohol, other drugs, and "
        "behavioural addictions. ICD-11 orders substance diagnoses by severity: hazardous "
        "use, a single episode of harmful use, a harmful pattern of use, and dependence, "
        "with alcohol at 6C40, cannabis at 6C41 and opioids at 6C43. That severity ladder "
        "matters for a workplace programme, because hazardous use is a brief-intervention "
        "target while dependence is a referral. Substance expertise is one of the "
        "historical defining features of employee assistance, and the EAPA Core Technology "
        "still names alcoholism and drug abuse explicitly among the conditions employee "
        "health benefits should cover.",
    ),
    (
        "MEDICAL_DISEASE_MGMT",
        "Medical Disease Mgmt",
        "The psychological and practical burden of physical illness, whether the member's "
        "own chronic or terminal condition or that of a relative they care for. The "
        "presenting problem is not the disease, which belongs to the treating clinician, "
        "but adjustment, adherence, anticipatory grief, caregiving strain and the effect "
        "on work capacity. WHO lists competing home and work demands among workplace "
        "psychosocial risks, and caregiving is the commonest form that takes in practice. "
        "Cases under this type frequently need coordination with a treating team and an "
        "accommodation conversation with the employer, which is EAPA Core Technology "
        "items 5 and 6 rather than counselling alone.",
    ),
    (
        "HEALTH_PROMOTION",
        "Health Promotion",
        "Preventive and educational contact where there is no presenting problem and no "
        "diagnosis: awareness sessions, lifestyle and fitness work, screening days, and "
        "general wellbeing support. Corresponds to the promotion function in EAPA Core "
        "Technology item 2, the active promotion of the availability of services to "
        "employees, their families and the organisation. WHO's supporting recommendations "
        "here are deliberately modest: training workers in mental health literacy is a "
        "conditional recommendation on very low-certainty evidence, and leisure-based "
        "physical activity likewise. Recorded as a type so that promotion volume is "
        "visible without contaminating clinical prevalence, since a talk attendee is not "
        "a case.",
    ),
    (
        "CHILD_TEENAGE",
        "Child & Teenage",
        "Presentations concerning a dependent child or adolescent, whether the child is "
        "the client or the employee is presenting a concern about them. WHO defines child "
        "maltreatment as all types of physical and emotional ill-treatment, sexual abuse, "
        "neglect, negligence and exploitation resulting in actual or potential harm to a "
        "child's health, survival, development or dignity in a relationship of "
        "responsibility, trust or power, and reports that 1 in 5 women and 1 in 7 men "
        "recall childhood sexual abuse. Any leaf here that names abuse triggers a child "
        "protection pathway, not only a clinical one: confidentiality is bounded by the "
        "duty to report, and that limit is explained to the family before the work "
        "begins. Non-abuse leaves cover school performance, bullying, and developmental "
        "and behavioural concerns.",
    ),
    (
        "GBV",
        "GBV (Gender-Based Violence)",
        "Violence and coercion directed at a person on the basis of gender, including "
        "intimate partner violence, sexual violence, harassment and coercive control. WHO "
        "defines intimate partner violence as behaviour by a partner or ex-partner causing "
        "physical, sexual or psychological harm, including physical aggression, sexual "
        "coercion, psychological abuse and controlling behaviours, and estimates in its "
        "2023 prevalence figures that about 31.6% of women, some 840 million, have "
        "experienced partner or non-partner sexual violence in their lifetime. ILO "
        "Convention 190, the Violence and Harassment Convention adopted in 2019, "
        "work free from violence and harassment including gender-based violence, which "
        "makes this an employer obligation and not only a member's private matter. Kept "
        "distinct from family and relationship conflict deliberately: safety planning, "
        "not reconciliation, is the first task, and couple work is contraindicated while a "
        "partner is unsafe.",
    ),
    (
        "FINANCIAL_WELLNESS",
        "Financial Wellness",
        "Money problems presenting as distress: debt, income shock, disputes over family "
        "finances, and the absence of financial literacy. Long-standing employee "
        "assistance scope rather than an addition, since work-based programmes routinely "
        "pair counselling with financial and legal consultation. WHO lists inadequate pay "
        "and job insecurity among workplace psychosocial risks, so the type also picks up "
        "distress the employer's own terms are producing. Sessions here are frequently "
        "advisory and signposting rather than clinical, and no mental disorder should be "
        "recorded unless one is independently present. Financial abuse within a "
        "relationship belongs under family and relationship, or under gender-based "
        "violence where it is part of coercive control.",
    ),
    (
        "BEHAVIOURAL_PERSONALITY",
        "Behavioural / Personality",
        "Enduring patterns of behaviour, coping and relating that cause the member "
        "difficulty across settings rather than in response to one event, together with "
        "adjustment difficulties that do not fit another type. ICD-11 replaced the "
        "categorical personality subtypes with a single personality disorder entity graded "
        "by severity, so a workplace programme should record the presenting pattern and "
        "refer for formal assessment rather than assign a subtype. In practice this type "
        "holds two different things: genuine personality-level difficulty, which is a "
        "referral, and behavioural or adjustment problems that respond to short-term work. "
        "Use it sparingly, because it is the type most likely to absorb a case that was "
        "simply hard to classify.",
    ),
    (
        "ADHD",
        "ADHD",
        "Attention deficit hyperactivity disorder, at ICD-11 6A05, with predominantly "
        "inattentive (6A05.0), predominantly hyperactive-impulsive (6A05.1) and combined "
        "(6A05.2) presentations, requiring symptoms evident across multiple settings for "
        "at least six months. Retained as its own type because adult ADHD arrives at "
        "workplace programmes as a performance and organisation problem rather than as a "
        "psychiatric complaint, and it needs a distinct pathway: screening, referral for "
        "formal assessment, then workplace accommodation. Its two leaves name "
        "interventions rather than conditions, which is a legacy of the source data and "
        "is being corrected; the condition itself is recorded under mental ill health. "
        "WHO strongly recommends reasonable work accommodations for workers with mental "
        "health conditions, which is the substance of what these cases need.",
    ),
    (
        "CHANGE_MANAGEMENT",
        "Change Management",
        "Adjustment to organisational change: restructuring, redundancy, merger, "
        "relocation, new leadership, or a new operating model. WHO names job insecurity "
        "and inadequate investment in career development among workplace psychosocial "
        "risks, so announced change is a predictable and forecastable spike in programme "
        "demand rather than a surprise. Distinguished from work stress by cause: the "
        "stressor is a discrete transition with a beginning and an end, not the standing "
        "conditions of the job. Cases here are usually short and group-deliverable, and "
        "the useful programme response is a talk plus individual sessions for those most "
        "exposed. A concentration of cases in one employer is evidence for an "
        "organisational conversation.",
    ),
    (
        "PERSONAL_GROWTH",
        "Personal Growth",
        "Self-development contact where the member has no presenting problem and is "
        "seeking capability: resilience, habits, self-management, confidence, and "
        "purpose. Recorded as a type so that developmental demand is visible and is not "
        "counted as clinical caseload. The evidence base is the same as for universal "
        "workplace promotion, where WHO conditionally recommends stress management "
        "interventions built on mindfulness or cognitive behavioural approaches for mental "
        "health promotion, on low-certainty evidence. No diagnosis should be recorded "
        "against this type. Where developmental work uncovers a clinical problem, the case "
        "is reclassified rather than kept here.",
    ),
]

# (type_code, code, name, description, is_active)
DIAGNOSES: list[tuple[str, str, str, str, bool]] = [
    # --- Addictions ---------------------------------------------------------
    (
        "ADDICTIONS",
        "ALCOHOL_AUD",
        "Abuse - Alcohol (AUD)",
        "Alcohol use causing harm to the member's health, relationships or work. ICD-11 "
        "grades disorders due to use of alcohol at 6C40 by severity: hazardous use, a "
        "single episode of harmful use, a harmful pattern of use where damage to physical "
        "or mental health is evident over at least 12 months episodically or one month "
        "continuously, and dependence at 6C40.2. That ladder decides the response: "
        "hazardous and early harmful use are brief-intervention targets a counsellor can "
        "work with, while dependence needs medical assessment and possible withdrawal "
        "management. Record which rung the presentation sits on, because prevalence "
        "counted without severity tells the employer nothing actionable.",
        True,
    ),
    (
        "ADDICTIONS",
        "SUBSTANCE_SUD",
        "Abuse - Substance (SUD)",
        "Use of a psychoactive substance other than alcohol causing harm, covering "
        "cannabis (ICD-11 6C41), opioids (6C43), stimulants, sedatives and inhalants. The "
        "same ICD-11 severity ladder applies as for alcohol, from hazardous use through a "
        "harmful pattern to dependence. Presentations often reach the programme indirectly, "
        "through absence, a performance concern raised by a manager, or a family member's "
        "call rather than the user's own request for help. Dependence and any suspected "
        "withdrawal risk are referrals for medical assessment, not counselling cases.",
        True,
    ),
    (
        "ADDICTIONS",
        "SEX_ABUSE",
        "Sex abuse",
        "Compulsive sexual behaviour presenting as an addictive pattern: loss of control "
        "over sexual impulses, escalating time and risk, and continuation despite harm to "
        "relationships or employment. ICD-11 recognises compulsive sexual behaviour "
        "disorder as an impulse control disorder rather than as an addiction, which is a "
        "distinction worth keeping in the notes even though the source vocabulary files it "
        "here. Distinct from sexual abuse perpetrated against another person, which is a "
        "safeguarding matter and belongs under the child and teenage or gender-based "
        "violence types. Where a disclosure indicates a victim, protection takes "
        "precedence over the therapeutic contract.",
        True,
    ),
    (
        "ADDICTIONS",
        "PRESCRIPTION_DRUG_ABUSE",
        "Prescription drug addiction/abuse",
        "Use of prescribed medication outside its prescription: escalating dose, use "
        "beyond the treated condition, obtaining supply from multiple prescribers, or "
        "continuation after the clinical need has passed. Most commonly opioid analgesics, "
        "benzodiazepines and sedatives, which fall under the ICD-11 substance groupings by "
        "class. Distinctive because the pathway into it is legitimate treatment, so members "
        "rarely present it as a substance problem and often frame it as pain or insomnia. "
        "Handled with the original prescriber where the member consents, since abrupt "
        "cessation of some of these medicines is itself a medical risk.",
        True,
    ),
    (
        "ADDICTIONS",
        "WORKAHOLIC",
        "Workaholic",
        "A compulsive pattern of overwork: inability to disengage, working through rest and "
        "leave, and distress when prevented from working, sustained despite harm to health "
        "and family life. Not a diagnosis in ICD-11, which is why it is recorded as a "
        "presenting pattern rather than a disorder. It is nonetheless a legitimate workplace "
        "finding, because it usually sits on top of the psychosocial risks WHO names, "
        "including excessive workload, unsocial hours and competing home and work demands. "
        "Often presents as exhaustion or family conflict rather than as a complaint about "
        "work, and it is worth distinguishing from burnout, which is the depletion that "
        "follows rather than the compulsion itself.",
        True,
    ),
    (
        "ADDICTIONS",
        "TECH_DIGITAL_ADDICTION",
        "Tech/digital addictions",
        "Compulsive use of digital technology: gaming, social media, streaming or "
        "pornography, continued despite loss of sleep, work performance or relationships. "
        "ICD-11 recognises gaming disorder at 6C51 as a disorder due to addictive "
        "behaviours, requiring impaired control, priority given to gaming over other "
        "activities, and continuation despite negative consequences, normally over at "
        "least 12 months. The wider category of general internet or social media addiction "
        "is not an ICD-11 disorder, so record what is observed rather than asserting a "
        "diagnosis. Frequently presents in dependants rather than employees, and pairs with "
        "the child and teenage digital effects leaf.",
        True,
    ),
    (
        "ADDICTIONS",
        "OTHER_ADDICTIONS",
        "Other addictions",
        "Addictive patterns that do not fit the named leaves of this type, most often "
        "gambling, shopping or food-related compulsion. ICD-11 recognises gambling "
        "disorder at 6C50 among disorders due to addictive behaviours; the others are "
        "recorded as presenting patterns rather than diagnoses. Retained deliberately as "
        "a residual leaf under a known type, which is different from a general unspecified "
        "bucket: the type is still reportable and the member is still counted in "
        "addictions prevalence. A rising count here means a leaf is missing and should be "
        "added rather than the bucket being widened.",
        True,
    ),
    (
        "ADDICTIONS",
        "BEHAVIOURAL_ADDICTION",
        "Behavioural addictions",
        "The broader grouping for addiction without a substance, covering the ICD-11 "
        "disorders due to addictive behaviours: gambling disorder at 6C50 and gaming "
        "disorder at 6C51. Used where the compulsive behaviour is established but has not "
        "been narrowed to one of the specific leaves, or where more than one behaviour is "
        "involved. Overlaps by design with the technology and other addictions leaves, "
        "which are the field vocabulary counsellors actually use; this leaf is the "
        "clinically framed parent. Prefer the specific leaf where the presentation "
        "supports it, and reserve this one for mixed or unnarrowed presentations.",
        True,
    ),
    # --- Career Challenges --------------------------------------------------
    (
        "CAREER_CHALLENGES",
        "STAGNATION",
        "Career stagnation",
        "The member's sense that their career has stopped moving: no progression, no new "
        "responsibility, and skills going unused. WHO names under-use of skills and "
        "inadequate investment in career development among the psychosocial risks at work, "
        "so this is a workplace finding and not only a personal disappointment. Sessions "
        "are coaching in character and should not carry a mental disorder unless one is "
        "independently present. A concentration of these cases in one employer or one "
        "department is worth reporting back as an organisational signal.",
        True,
    ),
    (
        "CAREER_CHALLENGES",
        "CAREER_FATIGUE",
        "Career fatigue",
        "Loss of motivation and interest in the career itself, as distinct from exhaustion "
        "caused by the current workload. The member typically still performs but has "
        "disengaged from any forward direction, and often describes wanting to leave "
        "without knowing what for. Kept under career challenges rather than work stress "
        "because the stressor is the trajectory rather than the conditions, which is a "
        "different intervention: direction-finding rather than load reduction. Where "
        "energy depletion, cynicism about the job and reduced efficacy dominate, consider "
        "burnout instead, which ICD-11 defines specifically in the occupational context.",
        True,
    ),
    (
        "CAREER_CHALLENGES",
        "DEMOTION",
        "Career demotion",
        "Distress following a reduction in role, grade, responsibility or status, whether "
        "as a disciplinary outcome, a restructuring consequence, or a performance "
        "decision. Carries a loss and a shame component that members rarely name directly, "
        "and it commonly presents as anger at the employer or as somatic complaint. WHO "
        "lists under- and over-promotion among workplace psychosocial risks, and job "
        "insecurity alongside it. The work is usually short: process the loss, separate "
        "the role from the self, and decide what happens next. Where the demotion followed "
        "a disciplinary process, the programme is a support rather than an appeal route, "
        "and that boundary is stated early.",
        True,
    ),
    (
        "CAREER_CHALLENGES",
        "CAREER_ASSESSMENT",
        "Career assessment/alignment/improvement",
        "Structured work on direction and fit: what the member is suited to, what they "
        "want, and how to close the gap. Delivered as assessment, coaching, or both, and "
        "the commonest non-clinical presentation in a wellness programme. No diagnosis "
        "should be recorded against it, since nothing clinical has been found. Where an "
        "employer commissions the assessment, what is fed back to the employer is agreed "
        "with the member before the work starts, because the same session cannot serve a "
        "confidential counselling contract and a selection decision.",
        True,
    ),
    (
        "CAREER_CHALLENGES",
        "CAREER_PROMOTION_COACHING",
        "Career promotion coaching",
        "Forward-looking coaching for a member preparing for or newly moved into a bigger "
        "role: readiness, interview and appraisal preparation, and the first months of a "
        "step up. Explicitly developmental rather than remedial, and it belongs in the "
        "wellness catalogue because WHO counts under-promotion and weak career investment "
        "among workplace psychosocial risks. Overlaps with career assessment, so use this "
        "leaf where a specific promotion or transition is in view and the other where the "
        "question is still open. Carries no diagnosis.",
        True,
    ),
]

DIAGNOSES += [
    # --- Child & Teenage ----------------------------------------------------
    (
        "CHILD_TEENAGE",
        "CHILD_SEX_ABUSE",
        "Child/teenage sex abuse",
        "Sexual abuse of a person under 18, whether disclosed by the child, by a parent, "
        "or suspected by a practitioner. Falls squarely within WHO's definition of child "
        "maltreatment, which covers sexual abuse occurring in a relationship of "
        "responsibility, trust or power and resulting in actual or potential harm to the "
        "child's health, survival, development or dignity; WHO reports that 1 in 5 women "
        "and 1 in 7 men recall childhood sexual abuse. A disclosure here starts a child "
        "protection pathway before a therapeutic one: the limits of confidentiality are "
        "explained to the family at the outset, and reporting duties are followed. "
        "Therapeutic work is trauma-focused and long, so the programme's realistic role is "
        "stabilisation, safety and referral rather than treatment.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "EMOTIONAL_ABUSE",
        "Child/teenage emotional abuse",
        "Persistent emotional ill-treatment of a child: humiliation, rejection, threats, "
        "scapegoating, or exposure to conflict and violence between adults. Named "
        "explicitly in WHO's definition of child maltreatment, which includes all types of "
        "emotional ill-treatment and neglect as well as physical and sexual abuse. Harder "
        "to evidence than physical harm and therefore under-reported, and it commonly "
        "presents as the child's behaviour or school performance rather than as abuse. WHO "
        "notes 6 in 10 children under five regularly experience physical punishment or "
        "psychological violence from parents and caregivers, so normalisation within the "
        "family is expected and must not be read as absence of harm.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "CHILD_LABOUR",
        "Child labour",
        "A child in work that is inappropriate for their age, interferes with schooling, or "
        "is harmful to their health or development. Sits within WHO's child maltreatment "
        "definition through its commercial and other exploitation clause. Usually presents "
        "indirectly, through school absence, fatigue or a parent's account of household "
        "economic pressure, so it is frequently entangled with the financial wellness type. "
        "Response is protection and referral to statutory and social services, not "
        "counselling alone, and the family's income situation has to be addressed for the "
        "protection plan to hold.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "CHILD_TRAUMA",
        "Child trauma",
        "A child or adolescent presenting after exposure to a threatening or horrific "
        "event: an accident, a violent incident, a death, or displacement. Distinguished "
        "from the trauma type's childhood trauma leaf by who is in the room: this leaf is "
        "for a child seen now, while the other records an adult presenting the legacy of "
        "childhood exposure. Where symptoms persist, ICD-11 post-traumatic stress disorder "
        "at 6B40 applies to children as it does to adults, and WHO's recommended "
        "treatments are trauma-focused cognitive behavioural therapy or EMDR. Single-session "
        "debriefing of a child after an event is not supported: WHO recommends strongly "
        "against psychological debriefing.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "SCHOOL_ISSUES",
        "Child/teenage school performance",
        "Declining or poor school performance as the presenting concern, whether raised by "
        "the parent or the school. Rarely the actual problem: it is the commonest visible "
        "symptom of most other leaves under this type, including abuse, bullying, parental "
        "separation, undiagnosed ADHD and child mental ill health. The useful first step is "
        "screening rather than academic support, so the assessment covers home, safety, "
        "peers, sleep and attention before any tutoring conversation. Record the underlying "
        "finding as the diagnosis once established, and keep this leaf for cases where "
        "performance is genuinely the whole picture.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "CHILD_TEACHER_RELATIONSHIP",
        "Child-teacher relationship",
        "Conflict or breakdown between a child and a teacher, including harsh discipline, "
        "humiliation in class, perceived unfairness, and fear of a particular teacher. "
        "Recorded separately from school performance because the intervention is different: "
        "it involves the school as a third party, and often the parent's advocacy rather "
        "than the child's coping. Where the teacher's conduct amounts to emotional or "
        "physical ill-treatment it becomes a maltreatment concern under WHO's definition, "
        "which covers harm in any relationship of responsibility, trust or power. Consent "
        "to contact the school is obtained from the parent before the programme acts.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "CHILD_BULLYING",
        "Child bullying",
        "Repeated aggression against a child by peers, in person or online, with a power "
        "imbalance the child cannot resolve alone. Associated with depression, anxiety, "
        "self-harm and school avoidance, and it frequently presents as somatic complaint or "
        "refusal to attend rather than as a report of bullying. The work has two halves: "
        "the child's safety and coping, and the school's response, which usually needs "
        "parental escalation. Cyberbullying overlaps with the digital effects leaf, and "
        "where the aggression is sexual it belongs under child sexual abuse with the "
        "protection pathway that follows.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "CHILD_PARENT_SEPARATION",
        "Child distress - parent separation/discord",
        "A child's distress arising from parental separation, divorce, or sustained conflict "
        "between parents in the home. WHO includes exposure to violence and conflict between "
        "adults within child maltreatment where it harms the child's development. Typically "
        "surfaces as behaviour change, school decline, regression or loyalty conflict rather "
        "than as stated sadness. Work is usually with the parents as much as the child, and "
        "the counsellor's task is to keep the child out of the middle rather than to resolve "
        "the adults' dispute, which belongs under the family and relationship type.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "TEENAGE_CHALLENGE",
        "Teenage challenge/confusion",
        "Adolescent developmental difficulty without a clinical diagnosis: identity, peer "
        "pressure, risk-taking, sexuality, autonomy conflict with parents, and uncertainty "
        "about the future. Recorded as a presenting concern rather than a disorder, because "
        "most of it is normal development that needs containment rather than treatment. Its "
        "value in the taxonomy is that it gives the counsellor somewhere honest to file a "
        "case that has no pathology, instead of reaching for a mental health leaf. Escalate "
        "to a clinical leaf where mood, psychosis, self-harm or substance use is present.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "CHILD_DIGITAL_EFFECTS",
        "Technological/digital effects",
        "Harm to a child from digital exposure: sleep loss, compulsive use, cyberbullying, "
        "harmful content, online grooming and contact from strangers. Overlaps deliberately "
        "with the technology addiction leaf under addictions, which records the compulsion "
        "itself; this leaf records the wider effects including those the child did not "
        "choose. ICD-11 recognises gaming disorder at 6C51 but not a general internet or "
        "social media addiction, so record observed harm rather than asserting a diagnosis. "
        "Any indication of grooming or sexual content involving the child moves the case to "
        "child sexual abuse and the protection pathway.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "CHILD_MENTAL_ILL_HEALTH",
        "Child mental ill-health",
        "A diagnosable mental disorder in a person under 18, including depression, anxiety, "
        "self-harm, psychosis and eating disorders. ICD-11 applies the same disorder "
        "categories to children as to adults, with developmental presentation differences, "
        "so this leaf marks the age of the client rather than a different clinical entity. "
        "Kept under the child and teenage type because the pathway is different: consent "
        "and confidentiality run partly through the parent, the school is often involved, "
        "and specialist child services are scarce. These are referrals with programme "
        "follow-up rather than cases the brief model closes.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "CHILD_SUBSTANCE_ABUSE",
        "Child drug/substance/alcohol abuse",
        "Alcohol or other drug use by a person under 18. The ICD-11 severity ladder applies "
        "as it does for adults, from hazardous use through a harmful pattern to dependence, "
        "with alcohol at 6C40 and cannabis at 6C41. Early onset is itself a risk marker for "
        "later dependence, so a presentation at this age warrants assessment rather than "
        "reassurance. Usually presents through a parent or school rather than the young "
        "person, which makes engagement the first clinical task; supply within the household "
        "and any adult-facilitated use are safeguarding questions.",
        True,
    ),
    (
        "CHILD_TEENAGE",
        "BEHAVIOURAL_ISSUES",
        "Behavioural issues",
        "Disruptive, defiant or aggressive behaviour in a child or adolescent that is "
        "persistent and out of keeping with their developmental stage. ICD-11 groups "
        "oppositional defiant disorder and conduct-dissocial disorder under disruptive "
        "behaviour and dissocial disorders, distinct from the neurodevelopmental grouping "
        "that holds ADHD. That distinction matters in practice because untreated ADHD and "
        "trauma both present as behaviour, and treating the behaviour alone leaves the "
        "cause in place. Screen for ADHD, maltreatment and home conflict before recording "
        "this as the finding.",
        True,
    ),
]

DIAGNOSES += [
    # --- Family & Relationship ---------------------------------------------
    (
        "FAMILY_RELATIONSHIP",
        "FAMILY_STRESS_BURNOUT",
        "Family stress, fatigue, burnout",
        "Depletion arising from family demands rather than from work: caregiving, "
        "parenting load, household economic pressure, and the absence of rest. Deliberately "
        "not recorded as burnout, because ICD-11 confines burn-out at QD85 to the "
        "occupational context and states it should not be applied to experiences in other "
        "areas of life. WHO does list competing home and work demands among workplace "
        "psychosocial risks, which is why family depletion is legitimately a workplace "
        "programme concern. Presents as exhaustion, irritability and reduced work "
        "performance, and the useful intervention is usually practical relief plus support "
        "rather than therapy.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "FAMILY_RELATIONSHIP_CONFLICT",
        "Family or relationship conflict",
        "Ongoing conflict within a couple or a family that has not resolved itself: "
        "arguing, withdrawal, disputes over money, in-laws, parenting or roles. The broadest "
        "leaf in the taxonomy and the default for relational distress that is not "
        "separation, infidelity or abuse. Conflict is distinguished from abuse by the "
        "presence or absence of fear and control: where one party is afraid, the case moves "
        "to relationship abuse or gender-based violence and couple work stops. Worked with "
        "either partner alone or with both, and useful outcomes are often clarity about the "
        "relationship's future rather than its repair.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "MARRIAGE_DIVORCE",
        "Marriage divorce",
        "Distress arising from the ending of a marriage, whether contemplated, in progress "
        "or complete, including the legal process, custody, property and the social "
        "consequences. Combines loss, conflict and practical crisis at once, which is why it "
        "commonly needs signposting to legal and financial help alongside counselling: "
        "work-based programmes routinely pair counselling with legal and financial "
        "consultation. Grief here is real but is not bereavement, and it responds to the same "
        "support without needing a grief diagnosis. Where children are involved, their "
        "distress is recorded separately under the child and teenage type.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "RELATIONSHIP_BREAKUP",
        "Relationship breakup",
        "The ending of an unmarried intimate relationship, including engagements, long-term "
        "partnerships and courtships. Recorded separately from divorce because the practical "
        "burden differs, with no legal process, while the emotional impact can be equivalent "
        "or greater in younger members. Frequently the presenting problem for a first contact "
        "with the programme, and it responds well to short-term work. Screen for suicidal "
        "ideation, since relationship loss is a common precipitant, and for stalking or "
        "coercion after the separation, which belongs under gender-based violence.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "RELATIONSHIP_CHEATING",
        "Relationship cheating/betrayal",
        "Infidelity or a comparable breach of trust, presented by either the injured or the "
        "involved partner. The clinical picture is often traumatic in character rather than "
        "simply distressed, with intrusive images, hypervigilance and rumination, and it is "
        "worth naming that to the member without recording a trauma diagnosis. Work is "
        "usually with the couple where both want the relationship to continue, and "
        "individually where the decision is still open. Confidentiality between partners is "
        "the recurring practical problem, and the rule on disclosures made in individual "
        "sessions is set before couple work begins.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "RELATIONSHIP_ABUSE",
        "Relationship abuse",
        "Abuse by an intimate partner where the presenting frame is the relationship rather "
        "than a safety referral. Matches WHO's definition of intimate partner violence: "
        "behaviour by a partner or ex-partner causing physical, sexual or psychological harm, "
        "including physical aggression, sexual coercion, psychological abuse and controlling "
        "behaviours. Retained under this type because that is how members and counsellors "
        "present it, but it is a safety case: risk assessment and safety planning come "
        "before any relational work, and couple counselling is contraindicated while a "
        "partner is unsafe. Cross-reference the gender-based violence type for reporting, "
        "since prevalence split across two types understates the problem.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "FAMILY_SEX_ABUSE",
        "Sex abuse (family/relationship)",
        "Sexual abuse or coercion within a family or intimate relationship where the person "
        "affected is an adult. WHO defines sexual violence as any sexual act or attempt to "
        "obtain a sexual act, or any act directed against a person's sexuality using "
        "coercion, by any person regardless of relationship to the victim, in any setting, "
        "and estimates about 8% of women aged 15 and over have experienced non-partner "
        "sexual violence. Named distinctly from the addictions leaf of the same short label "
        "so that a victim's case is never filed under a perpetrator's compulsion. Where the "
        "person affected is under 18, the case belongs under child and teenage sex abuse and "
        "the protection pathway.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "FAMILY_EMOTIONAL_ABUSE",
        "Emotional abuse",
        "Sustained psychological abuse of an adult within a family or intimate relationship: "
        "humiliation, threats, isolation, intimidation and degradation. Explicitly part of "
        "WHO's intimate partner violence definition, which names psychological abuse and "
        "controlling behaviours alongside physical aggression and sexual coercion. Members "
        "rarely name it as abuse, because without physical injury they doubt their own "
        "account, so the assessment asks about fear, permission-seeking and monitoring rather "
        "than about incidents. Treated as a safety case with the same risk assessment as "
        "physical abuse, since psychological abuse frequently precedes and accompanies it.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "FINANCIAL_ABUSE",
        "Financial abuse",
        "Control or exploitation of a person's money and economic independence by a partner "
        "or family member: withholding income, taking earnings, debt created in their name, "
        "or preventing them from working. A recognised form of controlling behaviour within "
        "WHO's intimate partner violence definition, and one of the strongest practical "
        "barriers to leaving an abusive relationship. Distinguished from the financial "
        "wellness type, which covers money problems the member owns; here another person is "
        "the cause. The response combines safety planning with concrete financial and legal "
        "signposting, since the member's exit depends on economic capacity.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "DOMESTIC_ABUSE_ASSAULT",
        "Domestic abuse/assault",
        "Physical violence or assault within the household, whether by a partner, an "
        "ex-partner or another family member. Falls within WHO's intimate partner violence "
        "definition where the perpetrator is a partner, and WHO's 2023 prevalence estimates "
        "put lifetime partner or non-partner sexual violence at about 31.6% of women "
        "globally, some 840 million people. Overlaps by design with the gender-based "
        "violence type's domestic violence leaf: this leaf reflects how the source data "
        "records it, and prevalence reporting should combine the two rather than read either "
        "alone. Immediate safety, medical attention and documentation of injury come before "
        "therapeutic work.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "MARITAL_CONFLICT",
        "Marital conflict",
        "Conflict specific to a marriage, as opposed to relational conflict generally: "
        "disputes over roles, money, extended family, intimacy and parenting within a "
        "marital contract. Retained alongside the broader family or relationship conflict "
        "leaf because the source vocabulary uses both, and because marriage carries legal "
        "and social consequences that change the member's options. Prefer this leaf where "
        "the couple is married and the wider one otherwise. As with all conflict leaves, the "
        "presence of fear or control moves the case out of conflict and into abuse.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "PARENTING_STRESS",
        "Parenting stress",
        "The strain of raising children: behaviour management, discipline decisions, "
        "school demands, single parenting, and guilt about availability. WHO lists competing "
        "home and work demands among workplace psychosocial risks, and parenting is the most "
        "common form. The distinction from the child and teenage type is who the client is: "
        "here the parent is the client and the child is the subject, and no diagnosis is "
        "recorded against the child. WHO's recommended response at population level is "
        "parental support programmes, which is a useful frame for what a workplace programme "
        "can offer as a group intervention.",
        True,
    ),
    (
        "FAMILY_RELATIONSHIP",
        "INTERGENERATIONAL_CONFLICT",
        "Intergenerational conflict",
        "Conflict between adult generations of a family: adult children with parents, "
        "in-laws, extended family obligations, and disputes over inheritance, care duties or "
        "cultural expectation. Distinct from parenting stress, where the child is a "
        "dependant, and from marital conflict, which is within the couple. Common where "
        "extended-family obligation is a strong social norm, and it frequently carries a "
        "financial dimension that belongs recorded alongside it. Work is usually with the "
        "member alone, since the wider family is rarely available to the programme.",
        True,
    ),
]

DIAGNOSES += [
    # --- Loss & Grief -------------------------------------------------------
    (
        "LOSS_GRIEF",
        "LOSS_OF_MONEY_PROPERTY",
        "Loss of money/property",
        "Grief following material loss: theft, fire, business failure, repossession, or "
        "loss of land or livestock. Recorded under loss rather than under financial "
        "wellness because the presenting problem is the grief reaction, not the budget, "
        "though the two frequently need working together. Often carries shame and a sense "
        "of failed obligation to dependants, which members disclose late. Where the loss "
        "followed a crime, screen for trauma as well, since robbery and fraud are named "
        "leaves under the trauma type.",
        True,
    ),
    (
        "LOSS_GRIEF",
        "LOSS_OF_LOVED_ONES",
        "Loss of loved ones",
        "Bereavement following the death of a family member, partner, friend or colleague. "
        "Grief is a normal response and the great majority of it needs support, not "
        "treatment, so no mental disorder is recorded by default. ICD-11 marks the boundary "
        "case as prolonged grief disorder at 6B42, requiring persistent longing for or "
        "preoccupation with the deceased accompanied by intense emotional pain and "
        "significant functional impairment continuing well beyond the loss, conventionally "
        "at least six months. The clinical test is duration and impairment rather than "
        "intensity, and a case that meets it is a referral rather than a longer course of "
        "brief counselling.",
        True,
    ),
    (
        "LOSS_GRIEF",
        "DISAPPEARANCE_OF_LOVED_ONES",
        "Disappearance of loved one",
        "A family member missing, abducted or unaccounted for, with no confirmed death. "
        "Clinically distinct from bereavement because the loss cannot be completed: there "
        "is no body, no certainty and no permission to mourn, which sustains hope and "
        "distress simultaneously. Practical needs, including police, legal and "
        "administrative processes, usually dominate the early sessions. Where the "
        "disappearance followed a violent event, the trauma type applies alongside this "
        "leaf, and the loss should not be reclassified as bereavement without confirmation.",
        True,
    ),
    # --- Medical Disease Mgmt ----------------------------------------------
    (
        "MEDICAL_DISEASE_MGMT",
        "CHRONIC_DISEASE",
        "Chronic disease management",
        "The psychological and practical burden of the member's own long-term physical "
        "condition: diabetes, hypertension, HIV, cancer, epilepsy, or a disability. The "
        "presenting problem is adjustment, adherence, disclosure at work and the effect on "
        "identity, not the disease itself, which belongs to the treating clinician. "
        "Depression and anxiety are common comorbidities and should be recorded separately "
        "where present rather than folded into this leaf. WHO strongly recommends "
        "reasonable work accommodations for workers with mental health conditions, and the "
        "same logic applies here: the useful output is often an accommodation conversation "
        "with the employer, with the member's consent.",
        True,
    ),
    (
        "MEDICAL_DISEASE_MGMT",
        "POOR_HEALTH_CONDITIONS",
        "Poor health conditions",
        "General ill health short of a named chronic diagnosis: recurrent illness, "
        "persistent pain, fatigue, poor sleep, and unexplained physical symptoms. ICD-11 "
        "recognises bodily distress disorder for persistent distressing physical symptoms "
        "with excessive attention to them, which is a referral question rather than "
        "something to assert in a counselling note. The leaf earns its place because these "
        "presentations are common, are not malingering, and often mask depression, anxiety "
        "or an undiagnosed condition. Refer for medical assessment before treating it as "
        "psychological.",
        True,
    ),
    (
        "MEDICAL_DISEASE_MGMT",
        "TERMINALLY_ILL_FAMILY",
        "Managing terminally ill family member/s",
        "Caring for a relative with a terminal or severe illness: the practical load, the "
        "anticipatory grief, and the effect on the member's work and health. WHO lists "
        "competing home and work demands among workplace psychosocial risks; caregiving is "
        "the version of that demand least visible to employers. Family interventions are "
        "part of WHO's recommended care in severe illness, so the useful service is often "
        "family therapy rather than individual counselling. Continues into bereavement, at "
        "which point the case moves to the loss and grief type rather than staying here.",
        True,
    ),
    # --- Mental Ill Health --------------------------------------------------
    (
        "MENTAL_ILL_HEALTH",
        "DEPRESSION",
        "Depression",
        "A depressive disorder, which WHO describes as depressed mood or loss of pleasure "
        "or interest in activities for long periods, with an episode lasting most of the "
        "day, nearly every day, for at least two weeks, alongside symptoms such as poor "
        "concentration, excessive guilt, hopelessness, disrupted sleep and low energy. WHO "
        "estimates 5.7% of adults globally have depression, around 332 million people, "
        "using 2021 Global Burden of Disease data, and roughly 1.5 times more women than "
        "men. Effective treatments exist and psychological treatment is first-line, "
        "including behavioural activation, cognitive behavioural therapy, interpersonal "
        "psychotherapy and problem-solving therapy, with antidepressants for moderate to "
        "severe cases. The two-week duration and daily persistence are what separate this "
        "from low mood, and applying that test is the difference between a diagnosis and a "
        "presenting concern.",
        True,
    ),
    (
        "MENTAL_ILL_HEALTH",
        "ANXIETY",
        "Anxiety",
        "An anxiety or fear-related disorder, which ICD-11 groups separately from mood "
        "disorders, covering generalised anxiety, panic disorder, social anxiety and "
        "specific phobias. WHO reports that depression and anxiety together account for an "
        "estimated 12 billion lost working days a year at about US$1 trillion in lost "
        "productivity, which makes this and depression the two conditions a workplace "
        "programme most needs to detect. Anxiety commonly presents somatically, as chest "
        "pain, breathlessness or gastrointestinal symptoms, so members often arrive via a "
        "medical route. Distinguish it from the work stress type: the stress type records "
        "distress caused by identifiable working conditions, this leaf records a disorder "
        "that persists independently of them.",
        True,
    ),
    (
        "MENTAL_ILL_HEALTH",
        "HALLUCINATIONS",
        "Hallucinations",
        "Perceiving something that is not there, which WHO describes as hearing, smelling, "
        "seeing, touching or feeling things that are not present. A symptom rather than a "
        "diagnosis, and it is retained as a leaf because counsellors need somewhere to "
        "record it before any diagnosis is established. Causes range across primary "
        "psychotic disorders, mood disorders with psychotic features, substance "
        "intoxication and withdrawal, and physical illness, so the correct response is "
        "urgent referral for medical and psychiatric assessment rather than a counselling "
        "plan. Where a diagnosis is later confirmed, the case should be recorded against "
        "that leaf and not left here.",
        True,
    ),
    (
        "MENTAL_ILL_HEALTH",
        "SUICIDAL_IDEATION",
        "Suicidal ideation",
        "Thoughts of ending one's life, ranging from passive wishes not to be alive to "
        "active planning and intent. WHO reports more than 720,000 suicide deaths a year "
        "and identifies a prior attempt as an important risk factor in the general "
        "population, which is why previous attempts are asked about directly. WHO's LIVE "
        "LIFE interventions are limiting access to means, responsible media reporting, "
        "fostering socio-emotional life skills in adolescents, and early identification, "
        "assessment, management and follow-up of anyone affected by suicidal behaviour: the "
        "last of these is the programme's job. Named ideation rather than suicide on "
        "purpose, because the record describes a living member at risk and conflating the "
        "two makes the register unreadable. Any case here requires a risk assessment, a "
        "safety plan, means restriction where possible, and same-day escalation when intent "
        "is present.",
        True,
    ),
    (
        "MENTAL_ILL_HEALTH",
        "SCHIZOPHRENIA",
        "Schizophrenia",
        "A primary psychotic disorder which WHO describes as causing psychosis and "
        "considerable disability, affecting personal, family, social, educational and "
        "occupational functioning. Features include persistent delusions, persistent "
        "hallucinations, experiences of thought control or influence, disorganised "
        "thinking, disorganised behaviour, negative symptoms such as social withdrawal and "
        "restricted emotional expression, and cognitive difficulty with memory, attention "
        "and problem-solving. WHO puts prevalence at roughly 1 in 345 people, about 0.29%, "
        "with onset most often in late adolescence and the twenties and earlier in men. "
        "Care is medication plus psychoeducation, family intervention, cognitive "
        "behavioural therapy, psychosocial rehabilitation and supported employment, so a "
        "programme's role is referral, family support and helping the employer sustain the "
        "member in work.",
        True,
    ),
    (
        "MENTAL_ILL_HEALTH",
        "BIPOLAR",
        "Bipolar",
        "A mood disorder which WHO describes as affecting mood, energy, activity and "
        "thought, characterised by manic or hypomanic and depressive episodes. Mania "
        "presents as extremely elevated mood with high energy, inflated self-worth, rapid "
        "speech, reduced need for sleep and risk-taking; depressive episodes match the "
        "depression picture, persisting most of the day nearly every day for at least two "
        "weeks. WHO estimates around 1 in 200 people, some 37 million, live with bipolar "
        "disorder as of 2021. Treatment is typically mood stabilisers or antipsychotics "
        "with psychological and psychosocial interventions including family "
        "psychoeducation, so this is a referral with programme follow-up. Members are "
        "frequently first seen in the depressed phase, so asking about past elevated "
        "periods is what prevents a misrecord as depression.",
        True,
    ),
    (
        "MENTAL_ILL_HEALTH",
        "ADHD_CONDITION",
        "ADHD (Attention Deficit Hyperactivity Disorder)",
        "Attention deficit hyperactivity disorder as a condition, at ICD-11 6A05, requiring "
        "manifestations of inattention or hyperactivity-impulsivity evident across multiple "
        "settings such as home, work and social life, for at least six months. ICD-11 "
        "records it by presentation: predominantly inattentive at 6A05.0, predominantly "
        "hyperactive-impulsive at 6A05.1, and combined at 6A05.2. In adults it typically "
        "reaches a workplace programme as disorganisation, missed deadlines, impulsive "
        "decisions or conflict rather than as a psychiatric complaint. Formal diagnosis "
        "requires specialist assessment, so the programme's contribution is screening, "
        "referral, and the workplace accommodation WHO strongly recommends for workers "
        "with mental health conditions.",
        True,
    ),
    (
        "MENTAL_ILL_HEALTH",
        "ADD_CONDITION",
        "ADD (Attention Deficit Disorder)",
        "Inattentive-type attention difficulty without prominent hyperactivity. ICD-11 does "
        "not recognise attention deficit disorder as a separate entity: what the label "
        "describes is coded as attention deficit hyperactivity disorder, predominantly "
        "inattentive presentation, at 6A05.0. Retained as a leaf because the term is in "
        "wide clinical and lay use in the source vocabulary and members present with it, "
        "but a referral letter should use the ICD-11 presentation rather than this label. "
        "Under-detected in adults and in women, because inattention without disruption "
        "rarely prompts referral in childhood.",
        True,
    ),
    (
        "MENTAL_ILL_HEALTH",
        "MENTAL_ILL_HEALTH_OTHERS",
        "Others",
        "A mental disorder that is established but does not match a named leaf under this "
        "type, for example an eating disorder, obsessive-compulsive disorder, a "
        "dissociative disorder or a neurocognitive disorder. Retained as a residual leaf "
        "under a known type rather than as a general unspecified bucket, so the case still "
        "counts in mental ill health prevalence and stays reportable. Record what the "
        "presentation actually is in the session notes, since the leaf name alone carries "
        "no clinical information. A rising count here means the taxonomy is missing a leaf "
        "and should gain one rather than absorb more into this.",
        True,
    ),
    (
        "MENTAL_ILL_HEALTH",
        "PTSD",
        "PTSD",
        "Retired duplicate. Post-traumatic stress disorder is recorded under the trauma "
        "type, where ICD-11 places it at 6B40 alongside complex post-traumatic stress "
        "disorder at 6B41. This leaf existed because the original seed listed PTSD under "
        "both types, which split the same condition across two prevalence buckets. Kept as "
        "an inactive row rather than deleted, because the taxonomy is versioned by design "
        "and a report produced earlier must still resolve the label it was built from. Use "
        "the trauma type's post-traumatic stress disorder leaf for all new records.",
        False,
    ),
]

DIAGNOSES += [
    # --- Trauma -------------------------------------------------------------
    (
        "TRAUMA",
        "TRAUMA_PTSD",
        "Post-traumatic stress disorder (PTSD)",
        "The ICD-11 disorder at 6B40, following exposure to an extremely threatening or "
        "horrific event, with re-experiencing the event in the present, deliberate "
        "avoidance of reminders, and persistent perceptions of heightened current threat. "
        "ICD-11 also carries complex post-traumatic stress disorder at 6B41 for repeated "
        "or prolonged trauma, commonly of childhood origin, which adds disturbances of "
        "affect regulation, negative self-concept and difficulty in relationships. WHO "
        "recommends individual or group trauma-focused cognitive behavioural therapy, EMDR, "
        "or stress management for adults with PTSD, and this is the single leaf in the "
        "taxonomy where the treatment modality is well specified. Not every trauma "
        "exposure produces the disorder, so reserve this leaf for cases meeting the "
        "criteria and use the exposure leaves below for the rest.",
        True,
    ),
    (
        "TRAUMA",
        "EMDR_INDICATED",
        "EMDR-indicated",
        "A flag that eye movement desensitisation and reprocessing is the indicated "
        "treatment, not a diagnosis. WHO recommends EMDR alongside trauma-focused "
        "cognitive behavioural therapy for adults with PTSD, and names it again in the "
        "context of stepping up when other approaches have not worked or are unavailable. "
        "Retained because the source vocabulary records it in the diagnosis field, but it "
        "describes an intervention: the diagnosis should be post-traumatic stress disorder "
        "or the relevant exposure leaf, with EMDR recorded as the treatment plan. Counting "
        "it as a diagnosis inflates trauma prevalence with treatment decisions, so it is a "
        "candidate for retirement once the treatment plan has a field of its own.",
        True,
    ),
    (
        "TRAUMA",
        "TRAUMA_ASSAULT",
        "Trauma - assault",
        "Exposure to physical or sexual assault by another person, whether a single "
        "incident or repeated. Interpersonal and intentional harm carries a higher risk of "
        "persistent post-traumatic symptoms than accidental exposure, so screen actively "
        "for the ICD-11 6B40 criteria at follow-up rather than assuming resolution. Where "
        "the assault was by a partner or family member the case also belongs under "
        "gender-based violence or family and relationship, and safety takes priority over "
        "trauma processing while the perpetrator has access. Immediate needs are medical "
        "attention, documentation, and reporting options explained without pressure.",
        True,
    ),
    (
        "TRAUMA",
        "TRAUMA_ROBBERY",
        "Trauma - robbery",
        "Exposure to robbery, armed hold-up or burglary, whether at work, in transit or at "
        "home. Common in banking, retail and cash-handling workforces, which makes it one "
        "of the few trauma leaves that arrives as a group of employees from a single "
        "incident. That must not be met with single-session psychological debriefing: WHO "
        "recommends strongly against psychological debriefing to reduce the risk of "
        "post-traumatic stress, anxiety or depressive symptoms after a traumatic event. "
        "What is supported is practical and social support, screening, and referral of "
        "those who develop symptoms into trauma-focused therapy.",
        True,
    ),
    (
        "TRAUMA",
        "TRAUMA_CHILDHOOD",
        "Childhood trauma",
        "An adult presenting the legacy of trauma sustained in childhood: abuse, neglect, "
        "violence in the home, or early loss. This is the presentation ICD-11 introduced "
        "complex post-traumatic stress disorder at 6B41 to describe, adding affect "
        "dysregulation, negative self-concept and interpersonal difficulty to the core PTSD "
        "features, and it is commonly associated with childhood abuse. WHO notes that "
        "adults with a history of childhood maltreatment carry elevated risk of depression, "
        "substance misuse, obesity and behavioural health problems, so comorbidity is the "
        "expectation rather than the exception. Complex presentations exceed a brief "
        "counselling model and should be referred with programme follow-up, and where the "
        "client is a child now, use the child and teenage type instead.",
        True,
    ),
    (
        "TRAUMA",
        "TRAUMA_WAR",
        "Trauma - war",
        "Exposure to armed conflict, insurgency, forced displacement or their aftermath, "
        "whether the member was a civilian, a combatant or a refugee. Typically involves "
        "repeated and prolonged exposure rather than a single event, which is the profile "
        "ICD-11 complex post-traumatic stress disorder at 6B41 was added for. Frequently "
        "accompanied by bereavement, loss of property and separation from family, so more "
        "than one type usually applies and the record should carry the primary presenting "
        "problem. These are referrals: the evidence-based treatments WHO recommends are "
        "trauma-focused cognitive behavioural therapy and EMDR, both beyond a brief model.",
        True,
    ),
    (
        "TRAUMA",
        "TRAUMA_ACCIDENT",
        "Trauma - accident",
        "Exposure to a road, industrial or domestic accident, as the person injured, a "
        "witness, or a first responder at the scene. Often combined with physical injury "
        "and a medical recovery, which delays the psychological presentation until "
        "rehabilitation is under way. Where the accident happened at work it also raises "
        "an occupational safety question for the employer, and a cluster of these cases is "
        "a finding worth reporting. Screen at follow-up for the ICD-11 6B40 criteria, "
        "particularly avoidance, which in road accidents shows up as an inability to drive "
        "or travel and directly affects work capacity.",
        True,
    ),
    (
        "TRAUMA",
        "TRAUMA_WORK_INCIDENT",
        "Trauma - work incidents (fraud/disciplinary/environment)",
        "Trauma arising from work events rather than from violence: being implicated in or "
        "investigated for fraud, a disciplinary process, a serious error, or a hostile work "
        "environment sustained over time. Whether these meet the ICD-11 6B40 threshold of "
        "an extremely threatening or horrific event is a clinical judgement and often they "
        "do not, in which case the work stress type is the accurate record. The leaf is "
        "retained because the experience is real and members present it as traumatic, and "
        "because it names an employer-side cause: WHO lists organisational culture that "
        "permits negative behaviour, bullying and harassment among workplace psychosocial "
        "risks. Handle the dual role carefully, since the employer commissioning the "
        "programme may also be the party investigating the member.",
        True,
    ),
    (
        "TRAUMA",
        "TRAUMA_UNCERTAINTIES",
        "Trauma - uncertainties (lack/poverty)",
        "Sustained distress from chronic deprivation and insecurity: poverty, food or "
        "housing insecurity, and the absence of any predictable future. Not a trauma "
        "diagnosis in ICD-11, which requires exposure to a threatening or horrific event, "
        "so this records a chronic adversity rather than an event. Retained because the "
        "source vocabulary uses it and because the presentation is genuine, frequently "
        "appearing as hopelessness and exhaustion that look like depression. Screen for "
        "depression and suicidal ideation, record those separately where present, and pair "
        "the case with the financial wellness type, since the practical need usually leads.",
        True,
    ),
    # --- Work Stress / Anxiety ---------------------------------------------
    (
        "WORK_STRESS_ANXIETY",
        "WORKPLACE_CONFLICT",
        "Work relationship conflict",
        "Conflict with a colleague or team that has not resolved itself: disputes, "
        "exclusion, breakdown of a working relationship, or persistent friction. WHO names "
        "weak colleague support and organisational culture that permits negative behaviour "
        "among workplace psychosocial risks, and where the conduct amounts to bullying or "
        "harassment it becomes an employer obligation under ILO Convention 190, the "
        "Violence and Harassment Convention adopted in 2019. The "
        "programme's role is the member's coping and options, not adjudication of the "
        "dispute, and that boundary is stated at the outset. A cluster of cases naming the "
        "same team is an organisational finding, which is what WHO's conditional "
        "recommendation on organisational interventions addresses.",
        True,
    ),
    (
        "WORK_STRESS_ANXIETY",
        "CHARACTER_ETHICS_MISALIGNMENT",
        "Work character/ethic/cohesion/misalignment challenges",
        "Distress arising from a mismatch between the member's values and what the job "
        "requires: pressure to act against their ethics, a culture they cannot align with, "
        "or loss of belief in the organisation's purpose. Includes moral distress, where "
        "the member knows the right action and is prevented from taking it, which is "
        "common in health and frontline roles. Not a disorder, and it should not be "
        "recorded as one; the useful outcome is often a decision about staying rather than "
        "symptom relief. Where the member is being asked to participate in wrongdoing, the "
        "session may raise reporting questions that sit outside the counselling contract.",
        True,
    ),
    (
        "WORK_STRESS_ANXIETY",
        "DIFFICULT_LEADER",
        "Work difficult leader/s",
        "Distress caused by a manager's conduct: micromanagement, unpredictability, public "
        "criticism, withholding of information, or intimidation. WHO names controlling "
        "management and limited control over job design among workplace psychosocial risks, "
        "and this is the leaf that most directly evidences them. It is also the strongest "
        "case for the intervention with the best evidence in the whole programme: WHO makes "
        "a strong recommendation, on moderate-certainty evidence, that managers be trained "
        "to support their workers' mental health. Where conduct crosses into harassment, "
        "ILO Convention 190 applies and the case is a workplace obligation rather than only "
        "a coping problem. Repeated cases naming one manager should be reported in "
        "aggregate without identifying members.",
        True,
    ),
    (
        "WORK_STRESS_ANXIETY",
        "WORK_STRIFE_TOXICITY",
        "Work strife/politics/toxicity",
        "Distress from the general climate of a workplace rather than one relationship: "
        "factionalism, favouritism, rumour, blame culture and pervasive insecurity. WHO "
        "lists organisational culture that permits negative behaviour, discrimination and "
        "exclusion, and job insecurity among the psychosocial risks, all of which describe "
        "this leaf. Individual counselling helps the member cope but cannot change the "
        "cause, which is why WHO's remedy is organisational: interventions that mitigate, "
        "reduce or remove the risk factor. A high count against one employer is a reporting "
        "obligation to that employer in aggregate, and it is the most useful thing a "
        "programme can offer here.",
        True,
    ),
    (
        "WORK_STRESS_ANXIETY",
        "PERFORMANCE_APPRAISAL",
        "Performance appraisal/challenges",
        "Distress connected to performance management: a poor rating, a formal improvement "
        "process, unclear or shifting expectations, or fear of an upcoming review. WHO "
        "names ambiguous job responsibilities and limited control over workload among "
        "workplace psychosocial risks, both of which commonly underlie an appraisal "
        "dispute. The programme supports the member through the process and does not "
        "arbitrate it, and where the employer is the client that distinction has to be "
        "explicit. Screen for depression and anxiety, since a sustained performance process "
        "is a common precipitant, and for whether an undetected condition is causing the "
        "performance problem in the first place.",
        True,
    ),
    (
        "WORK_STRESS_ANXIETY",
        "WORK_STRESS_FAMILY",
        "Work stress due to family relationship",
        "Work performance and wellbeing affected by problems at home, or home life "
        "affected by the demands of work. WHO lists competing home and work demands "
        "explicitly among the psychosocial risks at work, which is what this leaf records. "
        "It marks the interaction rather than either side alone, so the family cause should "
        "also be recorded under the family and relationship type where it is identified. "
        "Useful because it is the point at which the employer has a legitimate interest and "
        "an intervention available, most often flexibility or an accommodation, which WHO "
        "strongly recommends for workers with mental health conditions.",
        True,
    ),
    (
        "WORK_STRESS_ANXIETY",
        "BURNOUT",
        "Burnout",
        "Burn-out as ICD-11 defines it at QD85: a syndrome conceptualised as resulting from "
        "chronic workplace stress that has not been successfully managed, characterised by "
        "energy depletion or exhaustion, increased mental distance from the job or "
        "cynicism about it, and reduced professional efficacy. ICD-11 classifies it as an "
        "occupational phenomenon and not a medical condition, placing it in the chapter on "
        "factors influencing health status rather than among mental disorders, so it must "
        "not be recorded or reported as a mental illness. ICD-11 also confines it to the "
        "occupational context and states it should not be applied to experiences in other "
        "areas of life, which is why family depletion has its own leaf. All three "
        "dimensions should be present before recording it, and depression should be "
        "considered and excluded, since exhaustion alone does not distinguish them.",
        True,
    ),
]

DIAGNOSES += [
    # --- Health Promotion ---------------------------------------------------
    (
        "HEALTH_PROMOTION",
        "LIFESTYLE",
        "Lifestyle interventions",
        "Preventive work on nutrition, sleep, alcohol moderation, smoking and daily "
        "routine, where the member has no presenting disorder. Recorded so that preventive "
        "contact is visible in programme volume without being counted as clinical "
        "caseload. The supporting evidence is deliberately modest: WHO's recommendations "
        "on universal workplace promotion are conditional and rest on low or very "
        "low-certainty evidence, so this should be described to employers as promotion "
        "rather than treatment. No diagnosis attaches. Where lifestyle screening surfaces "
        "hazardous alcohol use, the case moves to the addictions type.",
        True,
    ),
    (
        "HEALTH_PROMOTION",
        "PHYSICAL_FITNESS",
        "Physical fitness counselling",
        "Support for physical activity as a mental health intervention: exercise guidance, "
        "activity challenges and fitness sessions. WHO conditionally recommends that "
        "opportunities for leisure-based physical activity be considered to improve mental "
        "health and work ability, on very low-certainty evidence. Kept under health "
        "promotion rather than treated as a clinical finding, and it should carry no "
        "diagnosis. The specific activity belongs in the session's topic field: recording "
        "a sport or a workout as a diagnosis is a data-quality error that inflates "
        "prevalence with entries that had no clinical content.",
        True,
    ),
    # --- GBV ----------------------------------------------------------------
    (
        "GBV",
        "DOMESTIC_VIOLENCE",
        "Domestic Violence",
        "Physical, sexual or psychological violence by a partner or ex-partner, recorded "
        "under gender-based violence so that it stays visible in safety reporting. WHO "
        "defines intimate partner violence as behaviour by a partner or ex-partner causing "
        "physical, sexual or psychological harm, including physical aggression, sexual "
        "coercion, psychological abuse and controlling behaviours, and its 2023 estimates "
        "put lifetime partner or non-partner sexual violence at about 31.6% of women, some "
        "840 million. WHO's recommended service response is protocols, trained staff, "
        "comprehensive care including mental and sexual and reproductive health, and "
        "coordinated referral to justice, social services and child protection. First "
        "priority is risk assessment and safety planning, not relationship work; couple "
        "counselling is contraindicated while a partner is unsafe.",
        True,
    ),
    (
        "GBV",
        "SEXUAL_HARASSMENT",
        "Sexual harassment",
        "Unwanted sexual conduct directed at the member, most often in the workplace: "
        "comments, propositions, touching, or conditioning work outcomes on sexual "
        "compliance. ILO Convention 190, the Violence and Harassment Convention adopted in "
        "2019, recognises the right of everyone to a world of work free from violence and "
        "harassment, including gender-based violence and harassment. That makes this an "
        "employer obligation, so a case here has a "
        "policy dimension as well as a clinical one. The member decides whether to report; "
        "the programme explains the options, documents carefully, and does not investigate.",
        True,
    ),
    (
        "GBV",
        "COERCIVE_CONTROL",
        "Coercive control",
        "A sustained pattern of domination without necessarily any physical violence: "
        "monitoring, isolation from family and friends, financial restriction, threats, and "
        "control of movement, appearance and contact. Named within WHO's intimate partner "
        "violence definition, which includes psychological abuse and controlling behaviours "
        "alongside physical aggression and sexual coercion. The most commonly missed "
        "presentation, because members without injuries doubt that what is happening counts "
        "as abuse, so the assessment asks about permission, fear and monitoring rather than "
        "incidents. A strong predictor of escalation, so a case here is treated with the "
        "same risk assessment as physical violence.",
        True,
    ),
    # --- Financial Wellness -------------------------------------------------
    (
        "FINANCIAL_WELLNESS",
        "DEBT_STRESS",
        "Debt stress",
        "Distress from borrowing the member cannot service: loans, salary advances, "
        "informal credit, arrears and the pressure of collection. WHO names inadequate pay "
        "and job insecurity among workplace psychosocial risks, so employer terms are part "
        "of the picture and not only the member's choices. Work-based programmes "
        "conventionally pair counselling with financial and legal consultation, and "
        "signposting to that practical help is usually the intervention that changes the "
        "situation. Screen for depression and suicidal ideation, since debt crisis is a "
        "recognised precipitant, and record those separately where present.",
        True,
    ),
    (
        "FINANCIAL_WELLNESS",
        "FINANCIAL_LITERACY",
        "Financial literacy",
        "Preventive and educational work on managing money: budgeting, saving, credit, "
        "insurance and planning. Developmental rather than clinical, and it carries no "
        "diagnosis, which is why it belongs in the taxonomy only as a record of what the "
        "contact was about. Commonly delivered as a group session under the empowerment or "
        "health talk services rather than one to one. Its value in a workplace programme "
        "is upstream: it reduces the debt crises that arrive later as clinical "
        "presentations.",
        True,
    ),
    (
        "FINANCIAL_WELLNESS",
        "FAMILY_FINANCE_DISPUTE",
        "Family finance disputes",
        "Conflict within a family about money: contested contributions, inheritance, "
        "school fees, support of extended family, or one member's spending. Distinguished "
        "from financial abuse, which is one person controlling or exploiting another's "
        "money and belongs under family and relationship or gender-based violence; here the "
        "dispute is between parties with comparable power. Common where extended-family "
        "obligation is a strong social norm, and it overlaps with intergenerational "
        "conflict. The useful output usually combines relational work with concrete "
        "financial signposting.",
        True,
    ),
    # --- Behavioural / Personality -----------------------------------------
    (
        "BEHAVIOURAL_PERSONALITY",
        "BEHAVIOURAL_PROBLEM",
        "Behavioural problem",
        "Behaviour causing the member difficulty at work or at home that is not accounted "
        "for by another leaf: anger, impulsivity, aggression, dishonesty or persistent "
        "rule-breaking. ICD-11 places disruptive behaviour and dissocial disorders in their "
        "own grouping, distinct from personality disorders and from the neurodevelopmental "
        "grouping that holds ADHD. That matters because undetected ADHD, substance use and "
        "trauma all present as behaviour, and recording the behaviour as the finding leaves "
        "the cause untreated. Screen those three before settling on this leaf.",
        True,
    ),
    (
        "BEHAVIOURAL_PERSONALITY",
        "PERSONALITY_ISSUES",
        "Personality issues",
        "Enduring patterns of thinking, feeling and relating that cause the member "
        "consistent difficulty across situations and over years, rather than in response "
        "to one event. ICD-11 replaced the categorical personality subtypes with a single "
        "personality disorder entity graded by severity as mild, moderate or severe, with "
        "optional trait qualifiers, so a subtype label should not be assigned in a "
        "counselling record. Formal diagnosis needs specialist assessment and the "
        "treatment is long, so this leaf marks a referral rather than a brief-model case. "
        "Use it sparingly: it is the leaf most likely to absorb a member the counsellor "
        "found difficult, which is a different thing from a diagnosis.",
        True,
    ),
    (
        "BEHAVIOURAL_PERSONALITY",
        "ADJUSTMENT_ISSUES",
        "Adjustment issues",
        "Difficulty adapting to an identifiable life change, with symptoms that are "
        "distressing and functionally limiting but do not meet the threshold for another "
        "disorder. ICD-11 places adjustment disorder at 6B43 among disorders specifically "
        "associated with stress, requiring a preoccupation with the stressor or its "
        "consequences and failure to adapt, usually resolving within about six months of "
        "the stressor ending. This is the most useful leaf in the taxonomy for honest "
        "recording, because it names real distress without asserting a mood or anxiety "
        "disorder. Where the change is organisational, the change management type is the "
        "more informative record.",
        True,
    ),
    # --- ADHD ---------------------------------------------------------------
    (
        "ADHD",
        "ADHD_ASSESSMENT",
        "Assessment",
        "The pathway record for arranging and following up a formal ADHD assessment: "
        "screening in the session, referral to a specialist able to diagnose, and receipt "
        "of the outcome. This names an intervention rather than a condition, which is a "
        "legacy of the source vocabulary; the condition belongs under mental ill health, "
        "where ICD-11 places attention deficit hyperactivity disorder at 6A05. Retained so "
        "that existing records and legacy spellings continue to resolve, and it is a "
        "candidate for retirement once assessment exists as a service in the catalogue. "
        "Do not report it in clinical prevalence, since it describes a referral step.",
        True,
    ),
    (
        "ADHD",
        "ADHD_COACHING",
        "Coaching",
        "The pathway record for ADHD-specific coaching: structure, planning, time "
        "management and workplace strategy for a member with diagnosed or suspected ADHD. "
        "As with the assessment leaf, this names an intervention rather than a condition, "
        "and the condition itself is recorded under mental ill health at ICD-11 6A05. It "
        "is the practical form that WHO's strong recommendation on reasonable work "
        "accommodations for workers with mental health conditions takes for this group. "
        "Retained for legacy resolution and a candidate for retirement once it exists as a "
        "service, and it should not be counted in clinical prevalence.",
        True,
    ),
    # --- Change Management --------------------------------------------------
    (
        "CHANGE_MANAGEMENT",
        "TRANSITION_STRESS",
        "Transition stress",
        "Distress during a defined organisational or role transition: a new manager, a new "
        "system, relocation, a merger, or a move between teams. WHO names job insecurity "
        "and inadequate investment in career development among workplace psychosocial "
        "risks, and announced change reliably converts them into programme demand. "
        "Distinguished from the work stress type by having a beginning and an expected end, "
        "which shapes the intervention towards containment rather than sustained coping. "
        "Where the distress persists well past the transition, adjustment issues or a mood "
        "disorder becomes the more accurate record.",
        True,
    ),
    (
        "CHANGE_MANAGEMENT",
        "REORG_ADJUSTMENT",
        "Re-org adjustment",
        "Adjustment during and after restructuring, including redundancy consultation, "
        "survivor guilt among those retained, and the increased load that follows a "
        "reduction in headcount. Concentrated by employer and by date rather than spread "
        "across the caseload, which makes it forecastable: a programme told about a "
        "restructure in advance can staff for it. WHO conditionally recommends "
        "organisational interventions that reduce psychosocial risk and strongly recommends "
        "reasonable accommodations for workers with mental health conditions, both of which "
        "belong in the employer conversation alongside individual sessions. Redundancy "
        "cases frequently need financial signposting as much as counselling.",
        True,
    ),
    # --- Personal Growth ----------------------------------------------------
    (
        "PERSONAL_GROWTH",
        "DAILY_HABITS",
        "Daily habits",
        "Work on routine and self-management where the member has no presenting problem: "
        "sleep, structure, exercise, screen use, planning and follow-through. Developmental "
        "rather than clinical, and no diagnosis should be recorded against it. The nearest "
        "supporting evidence is WHO's conditional recommendation on universal psychosocial "
        "interventions, where stress management built on mindfulness or cognitive "
        "behavioural approaches may be considered for mental health promotion, on "
        "low-certainty evidence. Where habit difficulty turns out to be sustained "
        "inattention or disorganisation across settings, screen for ADHD rather than "
        "continuing to work on habits.",
        True,
    ),
    (
        "PERSONAL_GROWTH",
        "EMOTIONAL_RESILIENCE",
        "Emotional resilience",
        "Building the member's capacity to tolerate and recover from stress before a "
        "problem arises: emotional regulation, self-awareness, boundary setting and "
        "recovery habits. Preventive and non-clinical, and it carries no diagnosis. Rests "
        "on the same conditional WHO recommendation as the habits leaf, which is worth "
        "stating plainly to employers who expect resilience training to substitute for "
        "reducing the psychosocial risk itself: WHO's recommendations on organisational "
        "intervention and reasonable accommodation are separate and are not replaced by "
        "training individuals. Commonly delivered as a group programme rather than one to "
        "one.",
        True,
    ),
]


def build() -> None:
    """Write the three import payloads."""
    OUT.mkdir(parents=True, exist_ok=True)
    types = [
        {
            "code": code,
            "name": name,
            "description": description,
            "sort_order": order,
            "is_active": True,
        }
        for order, (code, name, description) in enumerate(DIAGNOSIS_TYPES)
    ]
    order_of = {code: i for i, (code, _, _) in enumerate(DIAGNOSIS_TYPES)}
    per_type: dict[str, int] = {}
    diagnoses = []
    for type_code, code, name, description, is_active in DIAGNOSES:
        if type_code not in order_of:
            raise ValueError(f"{code} names an unknown type {type_code}")
        sort_order = per_type.get(type_code, 0)
        per_type[type_code] = sort_order + 1
        diagnoses.append(
            {
                "type_code": type_code,
                "code": code,
                "name": name,
                "description": description,
                "sort_order": sort_order,
                "is_active": is_active,
            }
        )
    diagnoses.sort(key=lambda d: (order_of[d["type_code"]], d["sort_order"]))
    services = [
        {
            "name": name,
            "description": description,
            "category": category,
            "duration_minutes": None,
            "is_group_service": is_group,
            "max_participants": None,
        }
        for name, category, is_group, description in SERVICES
    ]

    codes = [d["code"] for d in diagnoses]
    if len(codes) != len(set(codes)):
        raise ValueError("duplicate diagnosis code")
    names = [s["name"] for s in services]
    if len(names) != len(set(names)):
        raise ValueError("duplicate service name")

    for filename, payload in (
        ("diagnosis_types.json", types),
        ("diagnoses.json", diagnoses),
        ("services.json", services),
    ):
        (OUT / filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    print(f"diagnosis_types.json  {len(types)}")
    print(
        f"diagnoses.json        {len(diagnoses)} ({sum(1 for d in diagnoses if not d['is_active'])} inactive)"
    )
    print(
        f"services.json         {len(services)} ({sum(1 for s in services if s['category'])} categorised)"
    )


if __name__ == "__main__":
    build()

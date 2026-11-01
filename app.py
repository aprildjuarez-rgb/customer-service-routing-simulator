import re
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Magazine Subscriber Routing Simulator",
    page_icon="📚",
    layout="wide",
)

st.title("📚 Magazine Subscriber Customer Service Routing Simulator")
st.write(
    "Analyze subscriber questions received through email, phone, "
    "live chat, or web forms and recommend where they should go."
)

st.warning(
    "DEMO ONLY: This prototype uses keyword rules, not a trained AI model. "
    "Use fictional requests only. Never enter real subscriber personal, "
    "account, or payment information."
)

CATEGORIES = {
    "Subscription & Renewal": {
        "keywords": [
            "renew", "renewal", "expire", "subscription status",
            "subscription end",
        ],
        "team": "Subscription Services",
        "workflow": (
            "Check subscription status and term. Explain renewal options "
            "using approved procedures."
        ),
    },
    "Missing or Late Issue": {
        "keywords": [
            "missing issue", "missing magazine", "haven't received",
            "have not received", "never received", "didn't receive",
            "did not receive", "late issue", "damaged issue",
            "delivery problem",
        ],
        "team": "Fulfillment & Delivery",
        "workflow": (
            "Check the publication, issue, delivery window, and fulfillment "
            "status. Determine whether a replacement or other remedy applies."
        ),
    },
    "Address Change": {
        "keywords": [
            "address change", "change my address", "new address",
            "moving", "moved", "forward my magazine",
        ],
        "team": "Subscriber Account Services",
        "workflow": (
            "Follow identity-verification procedures before making an "
            "authorized address change."
        ),
    },
    "Billing & Payments": {
        "keywords": [
            "bill", "billing", "charged", "charge", "payment", "paid",
            "duplicate charge", "charged twice", "overcharged", "invoice",
            "credit card", "late fee", "price increase", "unexpected charge",
        ],
        "team": "Billing & Payments",
        "workflow": (
            "Verify the payment and subscription records. Investigate "
            "discrepancies and follow approval rules for adjustments."
        ),
    },
    "Digital Access": {
        "keywords": [
            "digital edition", "digital access", "can't log in",
            "cannot log in", "can't access", "cannot access",
            "password reset", "forgot my password", "login", "log in",
            "locked out", "read online", "tablet", "e-edition",
        ],
        "team": "Digital Subscriber Support",
        "workflow": (
            "Check digital-access eligibility and service status. Provide "
            "approved troubleshooting or secure account-recovery steps."
        ),
    },
    "Cancellation & Refund": {
        "keywords": [
            "cancel", "cancellation", "stop my subscription",
            "do not renew", "don't renew", "refund", "money back",
            "end my subscription",
        ],
        "team": "Retention & Account Services",
        "workflow": (
            "Explain the applicable cancellation policy. Verify refund "
            "eligibility and route exceptions for authorized review."
        ),
    },
    "Gift Subscription": {
        "keywords": [
            "gift subscription", "gift a subscription",
            "send as a gift", "gift magazine","as a birthday gift",
"for my mother",
"for someone else",
"gift recipient",
"subscription as a gift",
"purchase a subscription for",
        ],
        "team": "Subscription Sales",
        "workflow": (
            "Provide approved gift-subscription options, pricing, and "
            "delivery information."
        ),
    },
    "Complaint or Escalation": {
        "keywords": [
            "complaint", "manager", "supervisor", "third time",
            "still not fixed", "unresolved", "escalate", "unacceptable",
            "no one helped", "nobody helped", "multiple times",
            "very frustrated",
        ],
        "team": "Customer Service Escalations",
        "workflow": (
            "Acknowledge the concern, review prior contacts where authorized, "
            "assign an owner, and document the resolution plan."
        ),
    },
    "General Subscriber Question": {
        "keywords": [
            "gift", "how much", "price", "cost", "subscription options",
            "publication schedule", "how often", "customer service hours",
            "contact information", "what is included", "magazine format",
        ],
        "team": "General Subscriber Services",
        "workflow": (
            "Answer using the approved subscriber knowledge base. Ask for "
            "clarification if publication-specific information is needed."
        ),
    },
}

CHANNEL_GUIDANCE = {
    "Email": (
        "Use a clear subject and concise response. Confirm the next step "
        "and expected response time. Avoid sending sensitive account details."
    ),
    "Phone": (
        "Follow the approved identity-verification script before discussing "
        "account details. Document the call outcome."
    ),
    "Live chat": (
        "Give concise, step-by-step guidance. Verify identity before "
        "account-specific actions and transfer complex cases to a person."
    ),
    "Web form": (
        "Check that the submission contains enough information. Request "
        "clarification through an approved channel when needed."
    ),
}



def classify_request(message, channel, repeat_contact):
    text = re.sub(r"\s+", " ", message.lower()).strip()

    scores = {
        category: sum(
            1 for keyword in details["keywords"] if keyword in text
        )
        for category, details in CATEGORIES.items()
    }

    has_address = scores["Address Change"] > 0
    has_delivery = scores["Missing or Late Issue"] > 0
    has_digital = scores["Digital Access"] > 0
    has_billing = scores["Billing & Payments"] > 0
    has_cancellation = scores["Cancellation & Refund"] > 0

    # Detect a message containing both an address change and delivery issue.
    multiple_issues = has_address and has_delivery

    # Give specific requests precedence over incidental keywords.
    if repeat_contact or any(term in text for term in [
        "third time", "still not fixed", "manager", "supervisor",
        "complaint", "multiple times", "unresolved", "formal complaint"
    ]):
        category = "Complaint or Escalation"
    elif multiple_issues:
        category = "Needs Clarification"
    elif has_cancellation:
        category = "Cancellation & Refund"
    elif has_digital:
        category = "Digital Access"
    elif scores["Gift Subscription"] > 0:
        category = "Gift Subscription"
    elif has_billing:
        category = "Billing & Payments"
    else:
        precedence = [
            "Missing or Late Issue",
            "Address Change",
            "Subscription & Renewal",
            "General Subscriber Question",
        ]
        matched = [c for c in precedence if scores[c] > 0]
        category = (
            max(matched, key=lambda c: scores[c])
            if matched else "Needs Clarification"
        )

    if category == "Needs Clarification":
        team = "Subscriber Service Triage"
        workflow = (
            "The message may contain multiple requests or lacks enough "
            "detail. A person should clarify each issue and route it "
            "to the appropriate team."
        )
        confidence = "Low — clarification needed"
    else:
        team = CATEGORIES[category]["team"]
        workflow = CATEGORIES[category]["workflow"]
        confidence = (
            "Moderate" if scores[category] == 1 else "Higher (rule-based)"
        )

    # Elevate cancellation requests caused by unresolved delivery problems.
    cancellation_after_delivery = has_cancellation and has_delivery

    high_priority_terms = [
        "charged twice", "duplicate charge", "fraud", "unauthorized",
        "third time", "multiple times", "still not fixed", "manager",
        "supervisor", "urgent", "formal complaint", "unresolved",
        "last two", "two magazine issues",
    ]

    if (
        category == "Complaint or Escalation"
        or repeat_contact
        or cancellation_after_delivery
        or any(term in text for term in high_priority_terms)
    ):
        priority = "High"
        priority_reason = (
            "An escalation, repeat contact, unresolved delivery problem "
            "connected to cancellation, or potential high-impact issue "
            "was detected. Confirm priority against service-level rules."
        )
    elif category == "Needs Clarification":
        priority = "Normal — provisional"
        priority_reason = (
            "The request is unclear or may contain multiple issues. "
            "Confirm the request and impact before assigning a final priority."
        )
    elif category in [
        "General Subscriber Question", "Gift Subscription"
    ]:
        priority = "Low"
        priority_reason = "The request appears to be routine."
    else:
        priority = "Normal"
        priority_reason = (
            "No configured high-priority trigger was detected. Review "
            "publisher-specific service targets before final assignment."
        )

    payment_access_conflict = (
        has_digital
        and has_billing
        and any(term in text for term in [
            "paid", "payment", "inactive", "account says"
        ])
    )

    review_terms = [
        "refund", "credit", "charged", "charge", "cancel",
        "complaint", "manager", "supervisor", "fraud",
        "unauthorized", "identity theft", "lawyer", "lawsuit",
        "discrimination",
    ]

    human_review = (
        category in [
            "Complaint or Escalation",
            "Needs Clarification",
            "Cancellation & Refund",
        ]
        or repeat_contact
        or multiple_issues
        or payment_access_conflict
        or any(term in text for term in review_terms)
    )

    reasons = []

    if any(term in text for term in [
        "charged", "charge", "refund", "credit", "paid", "payment"
    ]):
        reasons.append("Payment or refund details may need verification.")

    if category == "Cancellation & Refund":
        reasons.append("Cancellation or refund policy may need review.")

    if category == "Complaint or Escalation":
        reasons.append(
            "A person should review the complaint and prior contacts."
        )

    if category == "Needs Clarification":
        reasons.append(
            "The request may contain multiple issues or needs clarification."
        )

    if repeat_contact:
        reasons.append(
            "Repeat contact may require continuity or escalation."
        )

    if multiple_issues:
        reasons.append(
            "A person should separate and route each request."
        )

    if payment_access_conflict:
        reasons.append(
            "The reported payment and inactive digital-access status "
            "should be checked."
        )

    if any(term in text for term in [
        "fraud", "unauthorized", "identity theft",
        "lawyer", "lawsuit", "discrimination"
    ]):
        reasons.append(
            "A potentially sensitive issue needs human assessment."
        )

    if not human_review:
        reasons.append(
            "Routine request; automated handling should only be used "
            "under approved procedures."
        )

    return {
        "Category": category,
        "Priority": priority,
        "Recommended team": team,
        "Recommended workflow": workflow,
        "Human review": "Yes" if human_review else "Not routinely required",
        "Review reason": " ".join(reasons),
        "Classification signal": confidence,
        "Priority rationale": priority_reason,
        "Channel guidance": CHANNEL_GUIDANCE[channel],
    }

    scores = {
        category: sum(
            1 for keyword in details["keywords"] if keyword in text
        )
        for category, details in CATEGORIES.items()
    }

    # Prefer specific service issues over broad general questions.
    precedence = [
        "Complaint or Escalation",
        "Billing & Payments",
        "Cancellation & Refund",
        "Missing or Late Issue",
        "Address Change",
        "Digital Access",
        "Subscription & Renewal",
        "Gift Subscription",
        "General Subscriber Question",
    ]

    matched = [c for c in precedence if scores[c] > 0]

    if repeat_contact or any(
        term in text
        for term in [
            "third time", "still not fixed", "manager",
            "supervisor", "complaint", "multiple times",
        ]
    ):
        category = "Complaint or Escalation"
    elif matched:
        category = max(matched, key=lambda c: scores[c])
    else:
        category = "Needs Clarification"

    if category == "Needs Clarification":
        team = "Subscriber Service Triage"
        workflow = (
            "Ask whether the request concerns delivery, billing, renewal, "
            "digital access, cancellation, or another subscription issue."
        )
        confidence = "Low — no configured category matched"
    else:
        team = CATEGORIES[category]["team"]
        workflow = CATEGORIES[category]["workflow"]
        confidence = (
            "Moderate" if scores[category] == 1 else "Higher (rule-based)"
        )

    high_priority_terms = [
        "charged twice", "duplicate charge", "fraud", "unauthorized",
        "third time", "multiple times", "still not fixed",
        "manager", "supervisor", "urgent",
    ]

    if category == "Complaint or Escalation" or repeat_contact or any(
        term in text for term in high_priority_terms
    ):
        priority = "High"
        priority_reason = (
            "An escalation, repeat contact, or potential high-impact issue "
            "was detected. Confirm priority against service-level rules."
        )
    elif category == "Needs Clarification":
        priority = "Normal — provisional"
        priority_reason = (
            "The issue is unclear. Confirm the request and impact before "
            "assigning a final priority."
        )
    elif category in [
        "General Subscriber Question", "Gift Subscription"
    ]:
        priority = "Low"
        priority_reason = "The request appears to be routine."
    else:
        priority = "Normal"
        priority_reason = (
            "No configured high-priority trigger was detected. Review "
            "publisher-specific service targets before final assignment."
        )

    review_terms = [
        "refund", "credit", "charged", "charge", "cancel",
        "complaint", "manager", "supervisor", "fraud",
        "unauthorized", "identity theft", "lawyer", "lawsuit",
        "discrimination",
    ]

    human_review = (
        category in ["Complaint or Escalation", "Needs Clarification"]
        or repeat_contact
        or any(term in text for term in review_terms)
    )

    reasons = []
    if any(term in text for term in ["charged", "charge", "refund", "credit"]):
        reasons.append("Payment or refund needs verification.")
    if "Cancellation" in category:
        reasons.append("Cancellation or refund policy may need review.")
    if category == "Complaint or Escalation":
        reasons.append("A person should review the complaint and prior contacts.")
    if category == "Needs Clarification":
        reasons.append("The request did not match a category reliably.")
    if repeat_contact:
        reasons.append("Repeat contact may require continuity or escalation.")
    if any(
        term in text
        for term in ["fraud", "unauthorized", "identity theft",
                     "lawyer", "lawsuit", "discrimination"]
    ):
        reasons.append("Potentially sensitive issue needs human assessment.")
    if not human_review:
        reasons.append(
            "Routine request; automated handling should only be used "
            "under approved procedures."
        )

    return {
        "Category": category,
        "Priority": priority,
        "Recommended team": team,
        "Recommended workflow": workflow,
        "Human review": "Yes" if human_review else "Not routinely required",
        "Review reason": " ".join(reasons),
        "Classification signal": confidence,
        "Priority rationale": priority_reason,
        "Channel guidance": CHANNEL_GUIDANCE[channel],
    }


st.sidebar.header("Sample requests")

samples = {
    "Missing magazine — email": (
        "Email",
        "I renewed my subscription, but I haven't received this month's issue.",
    ),
    "Duplicate charge — phone": (
        "Phone",
        "I was charged twice for my magazine renewal.",
    ),
    "Digital access — chat": (
        "Live chat",
        "I can't log in to read the digital edition on my tablet.",
    ),
    "Address change — web form": (
        "Web form",
        "I'm moving next week. How do I change my magazine address?",
    ),
    "Repeated complaint — email": (
        "Email",
        "This is the third time I've contacted support about my missing "
        "issue, and it still isn't fixed. I want a supervisor.",
    ),
    "Gift subscription — web form": (
        "Web form",
        "Do you offer gift subscriptions, and how much do they cost?",
    ),
    "Unclear request — chat": (
        "Live chat",
        "I need help with my subscription.",
    ),
}

sample_choice = st.sidebar.selectbox("Choose a sample", list(samples.keys()))

if st.sidebar.button("Load sample"):
    st.session_state["channel"] = samples[sample_choice][0]
    st.session_state["message"] = samples[sample_choice][1]

st.subheader("1. Enter the subscriber request")

col1, col2 = st.columns(2)

with col1:
    channel = st.selectbox(
        "Contact channel",
        ["Email", "Phone", "Live chat", "Web form"],
        key="channel",
    )

with col2:
    publication = st.text_input(
        "Magazine title (optional)",
        placeholder="Example: Sample Monthly",
    )

message = st.text_area(
    "Customer email, chat, web form, or phone-call summary",
    key="message",
    height=140,
    placeholder=(
        "Example: I renewed last month, but this month's magazine "
        "hasn't arrived."
    ),
)

repeat_contact = st.checkbox(
    "The subscriber has contacted us about this issue before"
)

if st.button("Analyze and recommend routing", type="primary"):
    if not message.strip():
        st.error("Please enter a fictional subscriber request.")
    else:
        result = classify_request(message, channel, repeat_contact)

        st.subheader("2. Routing recommendation")

        a, b, c = st.columns(3)
        a.metric("Issue category", result["Category"])
        b.metric("Priority", result["Priority"])
        c.metric("Human review", result["Human review"])

        st.markdown("### Recommended team")
        st.success(result["Recommended team"])

        st.markdown("### Recommended workflow")
        st.write(result["Recommended workflow"])

        st.markdown("### Priority rationale")
        st.write(result["Priority rationale"])

        st.markdown("### Human-review rationale")
        st.write(result["Review reason"])

        st.markdown("### Contact-channel guidance")
        st.write(result["Channel guidance"])

        st.caption(
            "Classification signal: "
            + result["Classification signal"]
            + ". This is not a calibrated probability."
        )

        if publication.strip():
            st.caption(
                f"Publication entered: {publication.strip()}. "
                "It has not been verified against a publisher system."
            )

        record = {
            "Timestamp": datetime.now().isoformat(timespec="seconds"),
            "Channel": channel,
            "Publication": publication.strip(),
            "Customer request": message,
            "Repeat contact": repeat_contact,
            **result,
        }

        csv = pd.DataFrame([record]).to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download this result as CSV",
            data=csv,
            file_name="subscriber_routing_result.csv",
            mime="text/csv",
        )

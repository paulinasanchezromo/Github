import os, json
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Creative Performance Agent", page_icon="🎮", layout="wide")
st.title("🎮 Creative Performance & Production Prioritization Agent")
st.caption("CSV performance analysis → AI hypotheses → prioritized production recommendations.")
REQ=["spend","impressions","clicks","installs"]
ALIASES={"creative_name":"creative","ad_name":"creative","asset":"creative","cost":"spend","media_spend":"spend","impr":"impressions","link_clicks":"clicks","app_installs":"installs","install":"installs","creative_format":"format","video_length":"duration_sec"}
def normalize(df):
    df=df.copy(); df.columns=[str(c).strip().lower().replace(" ","_") for c in df.columns]
    return df.rename(columns={c:ALIASES[c] for c in df.columns if c in ALIASES})
def analyze(df):
    df=normalize(df); missing=[c for c in REQ if c not in df.columns]
    if missing: return None,missing,[]
    for c in ["spend","impressions","clicks","installs","revenue"]:
        if c in df: df[c]=pd.to_numeric(df[c],errors="coerce").fillna(0)
    df["CTR"]=(df.clicks/df.impressions.replace(0,pd.NA)*100).fillna(0)
    df["CVR"]=(df.installs/df.clicks.replace(0,pd.NA)*100).fillna(0)
    df["CPI"]=(df.spend/df.installs.replace(0,pd.NA)).fillna(0)
    if "revenue" in df: df["ROAS"]=(df.revenue/df.spend.replace(0,pd.NA)*100).fillna(0)
    warnings=[]
    for col in ["impressions","clicks","installs"]:
        if (df[col]<=0).any(): warnings.append(f"Some rows have zero/missing {col}; related rates may be uninformative.")
    return df,[],warnings
def summary(df):
    s,i,c,k=df.spend.sum(),df.impressions.sum(),df.clicks.sum(),df.installs.sum()
    out=f"- Assets analyzed: {len(df)}\n- Spend: {s:,.2f}\n- Impressions: {i:,.0f}\n- Clicks: {c:,.0f}\n- Installs: {k:,.0f}\n- Aggregate CTR: {c/i*100 if i else 0:.2f}%\n- Aggregate CVR: {k/c*100 if c else 0:.2f}%\n- Aggregate CPI: {s/k if k else 0:.2f}"
    if "revenue" in df and df.revenue.sum()>0: out+=f"\n- Aggregate ROAS: {df.revenue.sum()/s*100 if s else 0:.1f}%"
    return out
def prompt_for(df,obj,limits,evidence):
    cols=[c for c in ["creative","format","hook","duration_sec","audience","country","spend","impressions","clicks","installs","CTR","CVR","CPI","revenue","ROAS"] if c in df.columns]
    return f"""You are a careful user-acquisition creative strategist. Recommend the next creative production decisions.
Objective: {obj}
Constraints: {limits}
Evidence summary:\n{evidence}
Rows (up to 100):\n{json.dumps(df[cols].head(100).round(3).to_dict(orient="records"),default=str)}
Return concise Markdown with headings: Executive recommendation, What the data says, Priority production tests, Risks and limitations, Human review gates, Reusable workflow.
Recommend at most 3 tests. For each include hypothesis, evidence, creative brief (hook, visual, message, CTA), success metric, validation plan, effort and confidence. Distinguish facts from hypotheses. Do not claim causality from observational data or invent missing metrics. Flag small samples. AI suggests; humans approve budget, IP/brand, localization and legal decisions."""
with st.sidebar:
    st.header("Decision context")
    objective=st.text_area("Primary objective","Improve UA efficiency while maintaining acquisition quality.")
    limits=st.text_area("Constraints","Limited production capacity; prioritize testable concepts and evidence.")
    model=st.text_input("OpenAI model",os.getenv("OPENAI_MODEL","gpt-4.1-mini"))
    st.caption("Add OPENAI_API_KEY in Railway Variables to enable AI.")
upload=st.file_uploader("Upload campaign CSV",type=["csv"])
if not upload:
    sample=pd.DataFrame([
      {"creative":"A Gameplay Hook","format":"Gameplay video","hook":"Action in first 3s","duration_sec":15,"spend":1200,"impressions":80000,"clicks":1600,"installs":240,"revenue":1800},
      {"creative":"B Character Reveal","format":"Character reveal","hook":"Character reveal","duration_sec":20,"spend":1500,"impressions":90000,"clicks":1350,"installs":270,"revenue":2400},
      {"creative":"C Cinematic","format":"Cinematic","hook":"Story opening","duration_sec":30,"spend":900,"impressions":75000,"clicks":525,"installs":105,"revenue":750},
      {"creative":"D Feature Demo","format":"Gameplay video","hook":"Feature demonstration","duration_sec":15,"spend":1100,"impressions":70000,"clicks":1260,"installs":252,"revenue":2100}])
    st.info("Upload the CSV supplied during the assessment. Required columns: spend, impressions, clicks, installs.")
    st.download_button("Download fictional sample CSV",sample.to_csv(index=False).encode(),"sample_campaign_data.csv","text/csv")
else:
    raw=pd.read_csv(upload); df,missing,warnings=analyze(raw)
    if missing:
        st.error("Missing required columns: "+", ".join(missing)); st.stop()
    for w in warnings: st.warning(w)
    st.caption("CTR = clicks/impressions; CVR = installs/clicks; CPI = spend/installs; ROAS = revenue/spend. Rates are calculated from the uploaded rows.")
    a,b,c,d=st.columns(4); spend=df.spend.sum(); imp=df.impressions.sum(); clicks=df.clicks.sum(); installs=df.installs.sum()
    a.metric("Spend",f"{spend:,.2f}"); b.metric("Installs",f"{installs:,.0f}"); c.metric("CTR",f"{clicks/imp*100 if imp else 0:.2f}%"); d.metric("CPI",f"{spend/installs if installs else 0:,.2f}")
    st.subheader("Analyzed data"); st.dataframe(df,use_container_width=True)
    st.download_button("Download analyzed CSV",df.to_csv(index=False).encode(),"creative_analysis.csv","text/csv")
    if st.button("Run AI analysis and generate priorities",type="primary"):
        evidence=summary(df); prompt=prompt_for(df,objective,limits,evidence)
        key=os.getenv("OPENAI_API_KEY","").strip()
        if not key:
            rec="# Executive recommendation\n\nAI was not run because OPENAI_API_KEY is missing.\n\n## What the data says\n"+evidence+"\n\nConfigure the key in Railway Variables and run again."
            st.warning("Set OPENAI_API_KEY in Railway Variables to enable model recommendations.")
        else:
            try:
                from openai import OpenAI
                client=OpenAI(api_key=key)
                rec=client.responses.create(model=model,input=prompt).output_text
            except Exception as e:
                rec="# AI request failed\n\n"+str(e)+"\n\n## Data summary\n"+evidence
                st.error("AI request failed; check model access and environment variables.")
        st.session_state["rec"]=rec; st.session_state["evidence"]=evidence
        st.session_state["time"]=datetime.utcnow().isoformat()+"Z"
    if "rec" in st.session_state:
        st.subheader("Recommendation"); st.markdown(st.session_state["rec"])
        st.download_button("Download recommendation.md",st.session_state["rec"].encode(),"recommendation.md","text/markdown")
        log=f"# Execution log\n\n- UTC timestamp: {st.session_state.get('time')}\n- Input file: {upload.name}\n- Rows: {len(df)}\n- Model: {model}\n- Objective: {objective}\n- Constraints: {limits}\n\n## Evidence summary\n{st.session_state.get('evidence','')}\n\n## Human review checklist\n- [ ] Verify calculations against source platform\n- [ ] Check attribution windows, currency and conversion definitions\n- [ ] Validate hypotheses with controlled tests\n- [ ] Human approval for brand/IP, localization, legal and budget\n"
        st.download_button("Download execution_log.md",log.encode(),"execution_log.md","text/markdown")

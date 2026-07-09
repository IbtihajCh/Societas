**SOCIETAS**

_A Multi-Agent Social Policy Simulation_

Complete Project Design Document | v1.0

**Theoretical Foundations**

_Alfred Adler · Karl Marx · Sigmund Freud · Abraham Maslow_

# **0\. Project Philosophy**

Societas is a multi-agent simulation of a living society. Every agent is a unique human being with a personality, needs, emotions, relationships, and a life that unfolds over time. The governing player enacts real-world policies - tax laws, welfare programmes, food subsidies, austerity - and observes how they cascade through a heterogeneous population. No two simulations are the same.

## **0.1 The Three Master Drives**

**Core Principle**

Everything in the simulation is ultimately downstream of three forces, synthesised from Adler, Marx, and Freud. These drives operate at all times and cannot be switched off - they can only be managed.

| **Drive**                       | **Source**    | **Manifestation in Simulation**                                                                                                   |
| ------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Power & Status                  | Alfred Adler  | Dominance urge, inferiority gap, jealousy, comparison with neighbours, reputation-seeking                                         |
| Material Resources              | Karl Marx     | Money, food, shelter, clothing - class determines life outcomes. Wealth inequality is structural.                                 |
| Pleasure / Pain (Lust / Unlust) | Sigmund Freud | The Unlust score drives irrational behaviour. High enough Unlust bypasses morality entirely. Thanatos activates destructive acts. |

## **0.2 Maslow's Hierarchy as Decision Architecture**

Maslow's pyramid is not just a conceptual reference - it is literally implemented as the agent decision priority queue. An agent satisfies lower-level needs before higher ones. The simulation currently focuses on concrete, measurable tiers and deliberately avoids abstract ones until v2.

| **Tier**               | **Layer**                                       | **Simulated?** | **Notes**                                                  |
| ---------------------- | ----------------------------------------------- | -------------- | ---------------------------------------------------------- |
| 1 - Physiological      | Food, water, sleep, sexual desire               | Yes - v1       | Core decay loop. Failure here = death.                     |
| 2 - Safety & Security  | Safety, employment, financial security, shelter | Yes - v1       | Largely determined by wealth class.                        |
| 3 - Love & Belonging   | Social connection, friendship, family, marriage | Partial - v1   | Friends, marriage basic. Full family v2.                   |
| 4 - Esteem             | Self-esteem, reputation, Adler inferiority gap  | Yes - v1       | Comparison engine implemented.                             |
| 5 - Self-Actualisation | Morality, creativity, purpose                   | Yes - v1       | Creativity as income modifier; morality as behaviour gate. |

# **1\. The Agent**

Every living entity in the simulation is an Agent. Agents are instantiated at world creation with randomised attributes drawn from realistic probability distributions (Beta, not uniform). All values that can change are called "dynamic" - they update every tick. Values set at birth and never changed are called "fixed traits".

## **1.1 Identity (Fixed at Birth)**

| **Attribute** | **Type / Range**       | **Notes**                                                     |
| ------------- | ---------------------- | ------------------------------------------------------------- |
| id            | Integer                | Unique identifier, sequential from 0                          |
| name          | String                 | Randomly generated; optional for display                      |
| gender        | M / F                  | Affects marriage compatibility and sexual tension resolution  |
| culture       | A / B / C (expandable) | Same-culture agents bond more easily, form communities faster |
| born_tick     | Integer                | Tick of birth. Age is derived: age = current_tick - born_tick |

## **1.2 Innate Traits (Fixed, Beta Distribution)**

**Why Beta Distribution?**

Uniform distributions produce unrealistic "flat" populations where extreme values are as common as moderate ones. Beta(2,2) gives a bell curve peaking at 0.5, meaning most agents are average with fewer extremes - matching real human populations.

| **Trait**      | **Distribution**       | **Low Value Means**                                              | **High Value Means**                                        |
| -------------- | ---------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------- |
| creativity     | Beta(2,2)              | Struggles to find solutions, may lose money                      | Earns more, finds opportunities, solves problems            |
| morality       | Beta(2,2)              | Harms others freely, steals without guilt, no prosocial acts     | Shares, consoles, never harms, helps even at cost to self   |
| anger_tendency | Beta(2,3) - skewed low | Slow to anger, absorbs frustration                               | Quick to anger, escalates to fight/kill at lower thresholds |
| extraversion   | Beta(2,2)              | Prefers isolation, social decay less painful, harder to befriend | Actively seeks social connection, befriends easily          |
| ambition       | Beta(2,2)              | Content where they are, less job-seeking drive                   | Pursues promotions, seeks higher education aggressively     |
| resilience     | Beta(2,2)              | Stays in negative emotion states longer                          | Recovers from sad/angry states faster                       |
| dominance_urge | Beta(2,2)              | Unaffected by others having more                                 | Strongly triggered by Adler comparisons; seeks status       |

## **1.3 Socioeconomic Status**

| **Attribute** | **Values**           | **Notes**                                                                            |
| ------------- | -------------------- | ------------------------------------------------------------------------------------ |
| wealth_class  | poor / middle / rich | Starting distribution: 50% poor, 35% middle, 15% rich. Derived from money over time. |
| money         | Float (£)            | Poor: £100-800. Middle: £2,000-8,000. Rich: £15,000-80,000 at birth.                 |
| base_salary   | Float (£/day)        | Derived from job category. Range within category, not a flat value.                  |
| employed      | Boolean              | Starting unemployment rate: 12%. Can change each tick.                               |
| education     | 0 / 1 / 2            | 0 = Lower/Primary. 1 = Secondary. 2 = Higher Education.                              |
| property      | Boolean              | Owns shelter. If False, renting costs money each tick. If no money, homeless.        |

### **Wealth Mobility Rules**

- Rich get richer: higher creativity and ambition compound earnings over time
- Education is expensive at each level - poor agents rarely access higher education without a scholarship
- Scholarship: random 2% chance per education cycle - genuinely random, as in reality
- Windfall events (rare): inheritance from distant relative, lucky discovery
- No explicit "social elevator" - mobility is possible but structurally difficult for the poor
- A highly creative poor agent has a higher chance of finding opportunities than a low-creativity poor agent

## **1.4 Maslow Needs (Dynamic, 0.0-1.0)**

Needs decay every tick. If any Layer 1 need reaches zero, the agent dies. Higher-layer needs degrading does not kill but pushes the agent toward negative emotion states and irrational behaviour.

### **Layer 1 - Physiological**

| **Need**       | **Decay Rate / Tick**               | **Replenished By**                                        | **Death if Zero?**         |
| -------------- | ----------------------------------- | --------------------------------------------------------- | -------------------------- |
| food           | 0.018 × scarcity_multiplier         | buy_food action; share action from others; beg action     | Yes                        |
| water          | 0.014 × scarcity_multiplier         | buy_food action (includes water); environment water level | Yes                        |
| sleep          | 0.010                               | rest action; automatic partial recovery each tick         | No - but worsens emotion   |
| sexual_tension | Builds at +0.008/tick if no partner | Marriage; resolved by partner interaction                 | No - contributes to Unlust |

### **Layer 2 - Safety & Security**

| **Need**           | **Decay Rate / Tick**                 | **Replenished By**                                    | **Key Modifiers**                        |
| ------------------ | ------------------------------------- | ----------------------------------------------------- | ---------------------------------------- |
| safety             | 0.004 + crime_pressure                | Community membership; police policy; befriend actions | Crime rate directly adds to decay        |
| financial_security | Derived from money buffer             | Employment + savings above threshold                  | Unemployment causes steep drop           |
| shelter            | Boolean - costs money/tick if renting | Property ownership; welfare housing policy            | Homelessness → rapid food/safety decline |

### **Layer 3 - Love & Belonging**

| **Need**          | **Decay Rate / Tick** | **Replenished By**                                | **Notes**                                              |
| ----------------- | --------------------- | ------------------------------------------------- | ------------------------------------------------------ |
| social_connection | 0.009                 | befriend, console, share, community interaction   | Extraverts decay slower; introverts need less baseline |
| family_bond       | 0.005                 | Interaction with spouse/children/parents/siblings | Bad emotions in family accelerate decay                |
| romantic_bond     | 0.006                 | Marriage; successful partner interaction          | Unmet → sexual_tension builds                          |

### **Layer 4 - Esteem**

| **Need**        | **Decay Rate / Tick**   | **Replenished By**                                        | **Notes**                                        |
| --------------- | ----------------------- | --------------------------------------------------------- | ------------------------------------------------ |
| self_esteem     | 0.003                   | Positive social interactions; good acts; job satisfaction | Adler comparisons can override gains immediately |
| reputation      | Passive decay: 0.001    | Good acts (share, console, befriend); community standing  | Criminal acts cause sharp drops                  |
| inferiority_gap | Computed on interaction | Downward comparison (agent sees someone worse off)        | Upward comparison increases Unlust directly      |

### **Layer 5 - Self-Actualisation**

| **Need**   | **Notes**                                                                                                                                             |
| ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| creativity | Fixed trait but acts as a modifier on economic outcomes. High creativity = income boost, problem-solving. Low = potential income loss.                |
| morality   | The defining behaviour gate of the simulation. High morality: agent considers others. Low morality: pure self-interest. Very low: Thanatos activates. |
| purpose    | Only meaningfully active when Layers 1-4 are adequately met (>0.6). If active, boosts creativity output and prosocial behaviours.                     |

## **1.5 The Unlust Engine (Freud's Pleasure Principle)**

**Core Mechanism**

Unlust is a master dissatisfaction score (0.0-1.0) computed every tick from unmet needs. When Unlust is low, agents behave rationally and morality applies fully. As Unlust rises, rational decision-making degrades. At maximum Unlust, all moral constraints are bypassed - the agent acts from pure base instinct. This is the computational implementation of Freud's Pleasure Principle.

Unlust only counts deficit below 0.5 - it measures how far below satisfactory each need is, not just being imperfect:

unlust = (max(0, 0.5−food)×0.28) + (max(0, 0.5−water)×0.22) + (max(0, 0.5−safety)×0.20) + (max(0, 0.5−social)×0.12) + (max(0, 1−(money/600))×0.18)

| **Unlust Range** | **State** | **Effect on Behaviour**                                            | **Morality Applied?**  |
| ---------------- | --------- | ------------------------------------------------------------------ | ---------------------- |
| 0.0 - 0.29       | Content   | Rational decision-making. Prosocial actions available.             | Fully                  |
| 0.3 - 0.57       | Stressed  | Emotional decisions dominate. Morality partially applies.          | Partially              |
| 0.58 - 0.81      | Driven    | Base instincts override. Anger/fear take control. Thanatos begins. | Only if morality > 0.6 |
| 0.82 - 1.0       | Desperate | Any action possible. Morality completely bypassed. Death risk.     | No                     |

## **1.6 Emotion State Machine**

Emotions are discrete states, not continuous scores. An emotion_timer creates hysteresis - once in an emotion state, the agent is locked for several ticks before re-evaluation. This prevents unrealistic flickering between states every tick. The resilience trait shortens the timer.

| **Emotion** | **Trigger Condition**                  | **Timer (ticks)**             | **Effect**                                                                |
| ----------- | -------------------------------------- | ----------------------------- | ------------------------------------------------------------------------- |
| happy       | happiness_score > 0.65                 | None (exits when score drops) | Productivity +20%, creativity +30%, social actions +40%, prosocial boost  |
| normal      | Default state (0.35-0.65 happiness)    | None                          | All baseline values apply, no modifiers                                   |
| sad         | happiness_score < 0.35                 | 2 ticks                       | Productivity −30%, creativity −20%, social actions −30%, partial morality |
| angry       | Unlust > 0.58 AND anger_tendency > 0.4 | 3 ticks                       | Protest/fight/harm become available. Morality gate weakened.              |
| despair     | Unlust > 0.82                          | 4 ticks                       | Isolates completely. Productivity near zero. Death risk 0.4%/tick.        |

### **Emotion Effect on Productivity & Creativity**

| **Emotion** | **Productivity Modifier** | **Creativity Modifier** | **Social Modifier**       |
| ----------- | ------------------------- | ----------------------- | ------------------------- |
| Happy       | +20%                      | +30%                    | +40%                      |
| Normal      | Baseline                  | Baseline                | Baseline                  |
| Sad         | −30%                      | −20%                    | −30%                      |
| Angry       | −10%                      | −10%                    | Harmful interactions only |
| Despair     | −60%                      | −50%                    | Isolation only            |

### **Sleep as Emotional Reset Mechanism**

- Sleep does not just boost mood - it is the mechanism by which emotional states decay back toward normal
- Agents with unmet needs sleep less (simulated insomnia), meaning negative states persist longer
- An agent in despair with poor sleep stays in despair far longer than one who sleeps well
- Sleep quality is a function of: safety_feeling × (1 − unlust) × resilience

## **1.7 Adler's Inferiority Complex - The Comparison Engine**

Every time an agent interacts with another, they compare Maslow scores. Upward comparison (other has more needs satisfied) triggers jealousy and increases Unlust. Downward comparison boosts self-esteem. This is why inequality is more dangerous than poverty alone - poor agents surrounded by wealthy neighbours feel worse than poor agents surrounded by equally poor ones.

| **Situation**                                         | **Effect on Agent**              | **Effect on Unlust** | **Dominance Urge** |
| ----------------------------------------------------- | -------------------------------- | -------------------- | ------------------ |
| Interacts with wealthier agent (gap > 1 Maslow level) | inferiority_gap ↑, self_esteem ↓ | +gap × 0.03          | +gap × 0.02        |
| Interacts with equally positioned agent (gap ≈ 0)     | No significant change            | No change            | No change          |
| Interacts with poorer agent (agent is better off)     | self_esteem ↑, inferiority_gap ↓ | −0.02                | −0.01              |

# **2\. Agent Lifecycle**

Agents are born, grow up, work, form families, age, and die. Each life stage has different needs, capabilities, and behavioural tendencies. The life cycle is one of the most complex systems and will be partially implemented in v2 - v1 starts agents as adults.

## **2.1 Age Brackets**

| **Bracket** | **Age Range** | **Key Characteristics**                                                                                                                  | **Resource Profile**                                    |
| ----------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Child       | 0-17          | Harmless, creative baseline high, shaped entirely by parents' emotional state, primary school phase, may drop out if home conditions bad | High money cost (education, food), low food consumption |
| Young Adult | 18-34         | Ambitious, fast emotion changes, high marriage drive, most likely to commit crimes, job-seeking aggressive                               | Normal money, high food consumption                     |
| Middle Aged | 35-49         | Emotionally stable, job loss hits very hard (major sadness trigger), rational decision-making predominates                               | Normal money and food                                   |
| Old         | 50+           | Emotionally unstable again, very unlikely to commit crimes, highest morality, low sexual desire, approaching death                       | Low food, takes money from children if no savings       |

## **2.2 Life Expectancy**

| **Condition**                        | **Life Expectancy Range**                 |
| ------------------------------------ | ----------------------------------------- |
| All needs well met, good health      | 85-100 years                              |
| Moderate unmet needs, average health | 60-75 years                               |
| Chronic poor health                  | 35-55 years                               |
| Very poor health                     | Can die randomly at any time              |
| Despair state (0.4%/tick mortality)  | Significant reduction to any of the above |

## **2.3 Birth & Death**

### **Birth Conditions**

- Requires: two agents of opposite gender who are married or in a stable partnership
- Requires: both agents have happiness_score > 0.5 AND basic needs met
- Child inherits traits as a random blend of both parents with slight mutation (±0.1)
- Birth triggers happiness boost to both parents
- If parents are frequently in angry/sad states, child replicates those states
- Child may drop out of education if home_environment_score < 0.3

### **Death Conditions**

- food = 0 or water = 0 (starvation)
- health ≤ 0 (chronic illness, fight damage)
- Despair state: 0.4% mortality chance per tick
- Life expectancy reached: probability-based death after max_age
- Fight outcome: loser may die depending on health and anger levels

### **Death Consequences for Others**

- Partner: prolonged sadness (emotion timer = 8), romantic_bond drops to 0
- Children: sadness (emotion timer = 5), family_bond drops
- Siblings: sadness (emotion timer = 3)
- Friends: mild sadness (emotion timer = 2)

## **2.4 Inheritance System**

| **Scenario**                       | **Distribution**                                             |
| ---------------------------------- | ------------------------------------------------------------ |
| Partner + children + parents alive | Partner: 30%, Children split: 40%, Parents split: 30%        |
| Partner + children only            | Partner: 40%, Children split: 60%                            |
| Partner + parents only             | Partner: 50%, Parents split: 50%                             |
| Partner only                       | 100% to partner                                              |
| Children only                      | 100% split equally among children                            |
| No one alive                       | Goes to community fund (redistributed as world welfare pool) |

**Rule:** The partner never receives more than 50% if other relatives are alive.

# **3\. Economy & Employment**

## **3.1 Job Categories**

**Design Rule**

Job availability is linked to population size. There are always fewer jobs than people, creating structural unemployment. Approximately: Technical jobs = 15% of jobs, Mid-tier = 35%, Manual = 50%. Job salaries are ranges, not flat values. A technical job may pay less than another technical job.

| **Job**              | **Category**   | **Education Required** | **Salary Range (£/year)** | **Special Effect**                                                         |
| -------------------- | -------------- | ---------------------- | ------------------------- | -------------------------------------------------------------------------- |
| Engineer             | Technical      | 2 - Higher             | 55,000-95,000             | None                                                                       |
| Computer Scientist   | Technical      | 2 - Higher             | 60,000-110,000            | None                                                                       |
| Pilot                | Technical      | 2 - Higher             | 50,000-90,000             | None                                                                       |
| Doctor               | Technical      | 2 - Higher             | 70,000-130,000            | Heals nearby agents each tick (+0.05 health)                               |
| Therapist            | Technical      | 2 - Higher             | 45,000-80,000             | 60% chance to calm angry/sad nearby agents; 40% risk if agent Unlust > 0.7 |
| Mechanic             | Technical-Hard | 1 - Secondary          | 25,000-45,000             | None                                                                       |
| Electrician          | Technical-Hard | 1 - Secondary          | 28,000-50,000             | None                                                                       |
| Construction Planner | Technical-Hard | 1 - Secondary          | 30,000-55,000             | None                                                                       |
| Construction Worker  | Manual         | 0 - Lower              | 12,000-22,000             | None                                                                       |
| Cleaner              | Manual         | 0 - Lower              | 10,000-18,000             | None                                                                       |
| Taxi Driver          | Manual         | 0 - Lower              | 11,000-20,000             | None                                                                       |

## **3.2 Education System**

| **Level**                  | **Cost**                       | **Gate**                                                        | **Outcome**                                             |
| -------------------------- | ------------------------------ | --------------------------------------------------------------- | ------------------------------------------------------- |
| Lower / Primary (Level 0)  | Low - covered by parents       | Automatic for children                                          | Access to manual jobs; baseline literacy                |
| Secondary (Level 1)        | Moderate - from parents' funds | Completion of Level 0; family can afford it                     | Access to technical-hard jobs; eligible for scholarship |
| Higher Education (Level 2) | High - significant expense     | Completion of Level 1; family can afford it or wins scholarship | Access to all technical jobs; highest salary potential  |
| Scholarship                | Free (replaces cost)           | Random 2% chance per education cycle - purely random            | Allows any wealth class to access higher education      |

- If parents cannot afford education and no scholarship: agent moves to next available job tier
- Children in bad home environments (home_environment_score < 0.3) may randomly drop out of lower education
- Dropping out results in: no formal job, beg or steal as primary income options

## **3.3 Money Flow**

| **Flow**           | **Trigger**                              | **Amount**                                         |
| ------------------ | ---------------------------------------- | -------------------------------------------------- |
| Income (work)      | Agent is employed, performs work action  | base_salary × (1 − tax_rate) × creativity_modifier |
| Food expenditure   | buy_food action                          | BASE_FOOD_COST × scarcity_multiplier               |
| Rent               | Every tick if no property                | Flat cost derived from wealth class                |
| Education cost     | Each education cycle                     | Varies by level; reduces parent money              |
| Children cost      | Every tick per child                     | Small flat cost, increases when school age         |
| Supporting parents | If morality > 0.5 and parents are old    | Small portion of income given to parents           |
| Welfare payment    | If welfare_enabled = True and unemployed | welfare_amount per tick (set by government)        |
| Stolen money       | Another agent steals                     | Up to 18% of victim's money, capped at £60         |
| Inheritance        | Another agent dies (relationship exists) | Per inheritance formula (Section 2.4)              |

# **4\. Agent Actions**

Every tick, each living agent selects exactly one action via the decision priority queue (Section 5). Actions have preconditions, outcomes, and side effects on other agents or the world.

## **4.1 Survival Actions**

| **Action** | **Precondition**              | **Primary Effect**                           | **Side Effects**                                            |
| ---------- | ----------------------------- | -------------------------------------------- | ----------------------------------------------------------- |
| work       | Employed = True               | money += salary × (1 − tax)                  | social += 0.015 (mild workplace contact)                    |
| buy_food   | money ≥ food cost             | food += 0.30, water += 0.20                  | money −= cost (scaled by scarcity)                          |
| rest       | energy < 0.2 OR despair state | sleep += 0.30, mood improves                 | Breaks out of angry state occasionally                      |
| seek_job   | employed = False              | Chance to become employed                    | Chance = 0.08 × (1 − unemployment_rate) × ambition modifier |
| beg        | money = 0 or near 0           | Small money gain from generous nearby agents | Receiving agent loses small money; dignity reduces slightly |

## **4.2 Social Actions**

| **Action**            | **Precondition**                                                     | **Effect on Agent**                                             | **Effect on Other**                                      |
| --------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------- |
| befriend(other)       | other not enemy, reputation > 0.25, compatible culture or random 25% | social += 0.12, Adler comparison triggered                      | social += 0.10, Adler comparison triggered               |
| marry(other)          | Opposite gender, not married, compatible emotional state             | romantic_bond established, sexual_tension → 0, shared resources | Same; combined resource pool                             |
| attract(other)        | No partner, opposite gender, reasonable compatibility                | Increases chance of marriage next interactions                  | May accept or reject based on their status needs         |
| gossip(other, target) | Has friend, is extraverted                                           | social += 0.05                                                  | Target's reputation ± depending on gossip content        |
| console(other)        | other is sad/despair, agent morality > 0.55                          | social += 0.05, good_acts++                                     | social += 0.08, emotion_timer reset - can recover faster |
| isolate               | Despair state                                                        | social −= 0.02 (further isolation)                              | None directly                                            |

## **4.3 Economic/Prosocial Actions**

| **Action**           | **Precondition**                                       | **Effect on Agent**                         | **Effect on Other / World**                          |
| -------------------- | ------------------------------------------------------ | ------------------------------------------- | ---------------------------------------------------- |
| share(other)         | morality > 0.68, money > 250, nearby needy agent       | money −= 6%, happiness += 0.04, good_acts++ | other gets money + food boost                        |
| invest               | wealth = rich/middle, money > threshold, ambition high | Passive money increase over time            | None                                                 |
| start_rumour(target) | dominance_urge high                                    | Self-esteem boost if successful             | Target reputation −= (damages their social standing) |
| seek_promotion       | Ambition high, employed                                | Chance of salary increase, good_acts++      | None                                                 |
| bribe                | wealth = rich, harmful policy active                   | Bypasses policy effect on self              | money −= bribe cost                                  |

## **4.4 Political Actions**

| **Action**   | **Trigger**                                              | **Effect**                                                                          | **Contagion?**                   |
| ------------ | -------------------------------------------------------- | ----------------------------------------------------------------------------------- | -------------------------------- |
| comply       | trust_in_govt > 0.6                                      | Absorbs policy effect passively                                                     | No                               |
| complain     | trust_in_govt < 0.4                                      | reputation += 0.02, spreads discontent to nearby agents                             | Yes - mild                       |
| protest      | Unlust > 0.45 AND emotion in (sad, angry)                | protest_count++, social += 0.06 (solidarity), spreads to nearby dissatisfied agents | Yes - strong (25% spread chance) |
| riot (group) | AUTO: triggered when >30% of population in angry/despair | Major world event. Crime surge. Safety crash across all agents.                     | Global                           |

## **4.5 Criminal Actions**

**Criminal Unlock Condition**

Criminal actions are not available by default. They unlock when: (Unlust > 0.58 AND morality_active() = False) OR (crimes_committed > 0, meaning the agent has already crossed that threshold once). Persistent criminals lose reputation and eventually become isolated from normal society.

| **Action**     | **Trigger**                                           | **Effect on Agent**                                         | **Effect on Victim / World**                                              |
| -------------- | ----------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------- |
| steal(other)   | food < 0.25 OR money < 50, morality inactive          | money += stolen, food += 0.08, crimes++, reputation −= 0.06 | victim money −= stolen, safety −= 0.12, victim becomes angry/scared       |
| argue(other)   | Both high anger but morality present                  | anger ↑ temporarily, then decays to sad, then normal        | Same - mutual anger escalation, then cool-down                            |
| fight(other)   | anger very high, morality low, other is enemy         | health risk, anger expression, crimes++                     | victim health −= 0.2+, victim angry, crime_rate ↑                         |
| kill(other)    | Unlust > 0.90, anger_tendency > 0.85, despair + fight | Removes victim from simulation, despair follows killer      | Global crime rate spike, agent becomes permanent enemy of victim's family |
| harm_other     | Thanatos drive: Unlust > 0.65, morality inactive      | crimes++, reputation −= 0.10, anger partially released      | victim safety −= 0.18, victim becomes angry                               |
| organize_crime | notoriety > 0.7, criminal_lean high, network exists   | Forms a criminal gang object. Passive income from crime.    | Crime rate sustained increase in zone                                     |

# **5\. Agent Decision Priority Queue**

Each tick, every living agent runs through this priority queue and executes the first matching action. This is a direct computational implementation of Maslow's hierarchy - lower needs always take priority over higher ones.

| **Priority**            | **Check**                                  | **Condition**                               | **Action Selected**                                                            |
| ----------------------- | ------------------------------------------ | ------------------------------------------- | ------------------------------------------------------------------------------ |
| 1 - Critical Survival   | Is food or water near zero?                | food < 0.08 OR water < 0.08                 | buy_food if money available. steal if morality inactive. beg as last resort.   |
| 2 - Emotional Override  | Is emotion state extreme?                  | emotion = despair                           | isolate()                                                                      |
| 2b - Emotional Override | Is emotion state extreme?                  | emotion = angry                             | protest (28% chance), harm_other (18% if no morality), steal (22% if food low) |
| 3 - Basic Food Need     | Is food below comfortable threshold?       | food < 0.35                                 | buy_food if money. steal if no morality. beg if moral.                         |
| 4 - Money / Employment  | Is agent unemployed?                       | employed = False                            | seek_job()                                                                     |
| 4b - Money              | Is money dangerously low?                  | money < 120                                 | work()                                                                         |
| 5 - Social Needs        | Is agent lonely and extraverted?           | social &lt; 0.38 AND extraversion &gt; 0.35 | befriend (55% chance)                                                          |
| 5b - Political          | Is agent dissatisfied with governance?     | unlust > 0.45 AND emotion in (sad, angry)   | protest (12% chance)                                                           |
| 6 - Prosocial           | Does agent have surplus and high morality? | morality > 0.68 AND money > 250             | share (18% chance) OR console (10% chance)                                     |
| 7 - Default             | None of the above triggered                | Always                                      | work()                                                                         |

**Morality Gate**

Before any criminal or harmful action is executed, morality_active() is checked. If Unlust &lt; 0.58: morality fully applies, blocking all criminal acts. If Unlust is 0.58-0.82 and morality &gt; 0.6: morality still blocks most acts. If Unlust > 0.82: morality is completely bypassed and any action is possible.

# **6\. Social Systems**

## **6.1 Reputation & Public Perception**

Reputation (0.0-1.0) is each agent's standing in society. It determines whether other agents will befriend, marry, or include them in a community. Low reputation leads to social isolation, which accelerates Unlust via unmet social needs - a death spiral that is realistic and observable.

| **Action Type**                      | **Reputation Effect**  | **Speed of Effect**     |
| ------------------------------------ | ---------------------- | ----------------------- |
| Good acts (share, console, befriend) | +0.02 to +0.05 per act | Slow accumulation       |
| Criminal acts (steal, fight, harm)   | −0.06 to −0.10 per act | Fast loss               |
| Kill another agent                   | −0.30 immediate        | Immediate and permanent |
| Passive decay                        | −0.001 per tick        | Very slow               |
| Community membership                 | +0.01 per tick         | Slow accumulation       |

### **Social Isolation Threshold**

- If reputation < 0.20: no agent will voluntarily befriend or marry this agent
- If reputation < 0.15: excluded from community formation or membership
- If reputation < 0.10: openly avoided - passing nearby causes safety drops in others
- Isolated agents face accelerated social decay → Unlust spike → more criminal behaviour → further reputation loss (reinforcing loop)

## **6.2 Friendship & Relationships**

| **Relationship Type**                | **Formation Condition**                                                 | **Benefits**                                                                                | **Breakdown Condition**                                               |
| ------------------------------------ | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| Friend                               | befriend action accepted; same culture preferred                        | social connection stabilised, mutual resource sharing possible, consoling available         | Criminal act against them; one becomes enemy; long separation         |
| Partner / Spouse                     | marry action; opposite gender; both have acceptable needs and happiness | Sexual tension resolved, romantic_bond, shared resource pool, happiness bonus               | Chronic bad emotions, needs very low, argument escalation             |
| Family (children, parents, siblings) | Born into / created by marriage + birth event                           | family_bond maintained, inheritance, emotional support                                      | Agent with very low morality may abandon family                       |
| Enemy                                | Fight outcome; theft by that agent; extreme argument                    | None - negative only                                                                        | Very rarely healed - requires high-morality console intervention      |
| Community                            | Emergent: same culture + similar wealth + frequent positive interaction | Higher social connection, safety in numbers, community sharing pool, faster befriend within | Community dissolves if culture mix drops or crime rate in group rises |

## **6.3 Community Formation (Emergent)**

- Communities are NOT pre-assigned - they form organically from repeated positive interactions
- Formation trigger: 3+ agents with same culture + similar wealth (within one class) + 5+ positive interactions
- Community benefits: agents interact more positively with community members than outsiders
- Inter-community tension: different communities with different culture values may conflict
- Sibling sub-community: siblings form the tightest possible community unit - most likely to share, but Adler jealousy is strongest between siblings (comparison to closest equals)
- Communities can dissolve if: crime rate within the group spikes; culture mix drops below threshold; average Unlust rises above 0.6

## **6.4 The Riot Event (Emergent Group Action)**

**Riot Trigger**

When ≥ 30% of the living population simultaneously holds emotion = angry or despair, a Riot event is automatically triggered. This is the most dramatic visible consequence of failed governance. Crime rate surges globally. All agents' safety drops. World food availability drops temporarily. The government is forced to respond.

# **7\. The World / Environment**

The World object is the environment that all agents inhabit. It maintains global state variables that agents read each tick. The environment is mostly neutral - it does not directly target agents - but its state changes (famine, drought) create pressure across the entire population simultaneously.

## **7.1 World State Variables**

| **Variable**       | **Range**       | **Default** | **Notes**                                                                                       |
| ------------------ | --------------- | ----------- | ----------------------------------------------------------------------------------------------- |
| food_availability  | 0.0-1.0         | 1.0         | Global food supply. Drops during famine/drought. Scarcity multiplier = 2.0 − food_availability. |
| water_availability | 0.0-1.0         | 1.0         | Global water supply. Droughts affect this.                                                      |
| crime_rate         | 0.0-1.0         | Computed    | Aggregate of all criminal actions normalised by population. Adds directly to safety decay.      |
| protest_intensity  | 0.0-1.0         | Computed    | Aggregate protest actions. Key governance feedback metric.                                      |
| unemployment_rate  | 0.0-1.0         | 0.12        | Affects job-finding probability each tick.                                                      |
| tax_rate           | 0.0-1.0         | 0.20        | Applied to all employed agents' salaries every tick.                                            |
| welfare_enabled    | Boolean         | False       | If True, unemployed agents receive welfare_amount per tick.                                     |
| welfare_amount     | Float (£)       | £8/tick     | Government-set. Adjustable via policy.                                                          |
| news_feed          | List of events  | \[\]        | Recent world events all agents passively absorb next tick.                                      |
| active_policies    | List of strings | \[\]        | Currently active government policies.                                                           |

## **7.2 Environmental Events**

| **Event**              | **Trigger**                  | **Effect**                                                   | **Duration**                        |
| ---------------------- | ---------------------------- | ------------------------------------------------------------ | ----------------------------------- |
| Minor food fluctuation | Random: 1.5%/tick chance     | food_availability ± 0.06-0.12                                | 1 tick (immediate adjustment)       |
| Famine / Drought       | Policy or random major event | food_availability drops 0.2-0.5                              | Multiple ticks until counter-policy |
| Abundance event        | Random or subsidy policy     | food_availability += 0.1-0.3                                 | Multiple ticks                      |
| Economic boom          | Tax cut + time               | unemployment_rate drops, average salary range increases      | Sustained                           |
| Economic crash         | Very high tax + austerity    | unemployment_rate rises, money decay accelerates             | Sustained                           |
| Riot aftermath         | \>30% angry/despair          | crime_rate surge, safety global drop, food_availability drop | 5-10 ticks                          |

## **7.3 Scarcity Multiplier**

When food_availability drops, the cost of buying food rises. This means economic shocks hit the poor hardest - they have less money buffer, so rising food prices starve them before the wealthy even feel the pinch.

food_cost = BASE_FOOD_COST × (2.0 − food_availability)

| **Food Availability** | **Scarcity Multiplier** | **Food Cost per Unit** |
| --------------------- | ----------------------- | ---------------------- |
| 1.0 (Abundant)        | 1.0×                    | Baseline (e.g., £6)    |
| 0.75                  | 1.25×                   | £7.50                  |
| 0.50 (Shortage)       | 1.50×                   | £9.00                  |
| 0.25 (Famine)         | 1.75×                   | £10.50                 |

# **8\. Governance Layer**

The governing player is a human or automated policy-maker who sits outside the simulation and enacts policies. Policies are not just number changes - they cascade through the world state → agent needs → agent emotions → agent actions → world metrics. The cascade is non-linear and emergent.

## **8.1 Policy Types & Expected Effects**

| **Policy**             | **Primary World Effect**     | **Poor Agents**                                | **Middle Agents**                         | **Rich Agents**                      |
| ---------------------- | ---------------------------- | ---------------------------------------------- | ----------------------------------------- | ------------------------------------ |
| Income tax increase    | tax_rate ↑                   | Hard hit - less money, less food buying        | Noticeable reduction in disposable income | Absorbs easily - lifestyle unchanged |
| Income tax cut         | tax_rate ↓                   | Small benefit (low salaries)                   | Moderate benefit                          | Large absolute benefit               |
| Introduce welfare      | welfare_enabled = True       | Major relief - anger drops, stealing drops     | Slight cost (funded by taxes)             | Dislikes funding it; mild anger      |
| Cut welfare/austerity  | welfare_enabled = False      | Immediate crisis - food drops, stealing spikes | Mild negative                             | Slight positive (lower taxes)        |
| Food subsidy           | food_availability ↑          | Significant food relief                        | Moderate relief                           | Negligible impact                    |
| Police/security policy | crime_rate decay ↑           | Safety improves                                | Safety improves                           | Safety improves - all benefit        |
| Education funding      | Scholarship rate ↑           | Access to higher education opens               | Moderate benefit                          | Already accessing - minimal change   |
| Housing policy         | property access ↑            | Homelessness drops, safety improves            | Moderate benefit                          | No impact                            |
| Minimum wage law       | Salary floor for manual jobs | Direct income boost                            | No change                                 | Slight cost (employs them)           |

## **8.2 The Cascade Mechanism**

**Example cascade - "Cut welfare spending":**

| **Step**                  | **What Happens**                                                                     |
| ------------------------- | ------------------------------------------------------------------------------------ |
| 1\. Policy enacted        | welfare_enabled = False. All unemployed poor agents lose welfare income immediately. |
| 2\. World state update    | unemployment_rate pressure increases. food_availability indirectly pressured.        |
| 3\. Agent needs update    | Poor agents: money → 0. food_cost exceeds money. food begins falling below 0.35.     |
| 4\. Unlust computation    | food deficit + money stress → Unlust spikes past 0.58 for many poor agents.          |
| 5\. Emotion state update  | Poor agents transition: normal → sad → angry. Anger_tendency determines which.       |
| 6\. Action selection      | Priority 1/2 triggered: steal and protest actions selected by many poor agents.      |
| 7\. Crime rate rises      | aggregate crimes_committed rises → world crime_rate metric rises.                    |
| 8\. Safety spreads        | Rising crime_rate adds to safety_decay for ALL agents - including rich and middle.   |
| 9\. Middle class reacts   | safety < 0.5 for middle class → they complain → protest_intensity rises.             |
| 10\. Rich agents react    | Safety drop triggers minor emotional response. They bribe or seek private security.  |
| 11\. Riot threshold check | If >30% angry/despair → global riot event triggers.                                  |
| 12\. Government feedback  | protest_intensity and crime_rate visible to governing player. Must respond.          |

## **8.3 LLM Policy Evaluation**

When a natural language policy is enacted (e.g., "raise income tax by 10%"), it is sent to a large language model (Claude API) for evaluation. The LLM receives the policy text and current world state, and returns a structured JSON object of impact deltas per wealth class.

**LLM as Qualitative → Quantitative Translator**

The LLM's role is not to generate text - it is to translate qualitative policy descriptions into realistic, context-sensitive numerical impact deltas. This means the same policy ("tax increase") has different magnitudes depending on the current state of the world: a tax increase during famine is more devastating than one during abundance.

### **Impact Delta Schema (per wealth class)**

| **Field**    | **Type**           | **Range**      | **Meaning**                        |
| ------------ | ------------------ | -------------- | ---------------------------------- |
| money_delta  | Float              | −50 to +50     | Immediate daily money change (£)   |
| food_delta   | Float              | −0.20 to +0.20 | Change in food need satisfaction   |
| safety_delta | Float              | −0.20 to +0.20 | Change in safety feeling           |
| social_delta | Float              | −0.10 to +0.10 | Change in social cohesion          |
| anger_spike  | Float              | 0.0 to +0.30   | Immediate Unlust/anger increase    |
| new_tax_rate | Float (optional)   | 0.05-0.60      | If policy changes tax rate         |
| welfare_on   | Boolean (optional) | True/False     | If policy enables/disables welfare |
| food_event   | Float (optional)   | −0.40 to +0.40 | Direct world food supply change    |
| reasoning    | String             | 1 sentence     | LLM's reasoning (logged for audit) |

# **9\. Evaluation Metrics & Visualisation**

## **9.1 World-Level Metrics (Tracked Per Tick)**

| **Metric**          | **Computation**                               | **Governance Meaning**                                                                     |
| ------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------ |
| avg_happiness       | Mean happiness_score across all living agents | Primary wellbeing indicator. The governing player's "approval rating".                     |
| avg_unlust          | Mean Unlust across all living agents          | Leading indicator - rises before visible behaviour changes. The best early warning system. |
| crime_rate          | Total crimes / (alive × 8)                    | Societal instability. If rising, governance is failing the bottom of the pyramid.          |
| protest_intensity   | Total protests / (alive × 4)                  | Political unrest. Governance feedback signal.                                              |
| unemployment_rate   | Unemployed / alive                            | Economic health indicator.                                                                 |
| alive_count         | Count of alive = True agents                  | Ultimate survival metric - policies that kill people are catastrophic.                     |
| food_availability   | Direct world state value                      | Environmental health. Drops during crises.                                                 |
| emotion_proportions | Count per emotion / alive for each emotion    | Population mood distribution. Stacked area chart shows shifts clearly.                     |
| action_frequencies  | Count per action / total actions per tick     | What the population is actually doing. Steal/protest surge = governance failure.           |

## **9.2 Wealth-Stratified Analysis**

A key analytic capability is breaking any metric down by wealth class. The same policy appears very different when viewed class-by-class. This is the primary analytical output for evaluating whether policies are equitable or regressive.

| **Breakdown Available** | **By Class (Poor/Middle/Rich)** | **Meaning**                                                         |
| ----------------------- | ------------------------------- | ------------------------------------------------------------------- |
| Average happiness       | Yes                             | Are the poor getting happier or just the rich? Policy equity check. |
| Crime rate              | Yes                             | Is crime concentrated in the poor? Or spreading to middle class?    |
| Emotion distribution    | Yes                             | How many poor agents are in despair vs happy rich agents?           |
| Employment rate         | Yes                             | Is unemployment concentrated in lower classes?                      |
| Money distribution      | Yes - histogram                 | Lorenz effect: wealth gap widening or narrowing over time?          |

## **9.3 Visualisation Dashboard**

| **Panel**              | **Content**                                                                     | **Key Feature**                                                            |
| ---------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Agent Grid             | N×N grid. Each dot = one agent. Colour = emotion state. Size = relative wealth. | Real-time view of spatial distribution of emotion. Crime clusters visible. |
| Needs & Unlust         | Line chart: happiness, food, safety, social, unlust over time                   | Red dashed vertical lines mark every policy enactment. Before/after clear. |
| Emotion Distribution   | Stacked area chart: proportion of population in each emotion state              | Policy shocks visible as sudden shifts in the stacked areas.               |
| Instability Indicators | Crime rate, protest intensity, unemployment over time                           | The governance failure signal panel.                                       |
| Population & Wealth    | Alive count (bar/line) + average money (dual axis)                              | Shows population survival + economic health together.                      |
| Action Frequencies     | Proportion of each action per tick: work, steal, protest, share, befriend       | Most direct view of what the policy is actually causing agents to do.      |

# **10\. System Architecture**

## **10.1 Layered Architecture**

| **Layer**           | **Component**                         | **Responsibility**                                                               |
| ------------------- | ------------------------------------- | -------------------------------------------------------------------------------- |
| Governance Layer    | Human player / automated policy-maker | Enacts policies via natural language. Reads feedback metrics. Iterates.          |
| LLM Impact Engine   | Anthropic Claude API (claude-sonnet)  | Translates policy text → structured JSON impact deltas per wealth class.         |
| Rule-Based Fallback | Keyword-matching policy interpreter   | Used when LLM unavailable. Parses known policy keywords deterministically.       |
| World / Environment | World class                           | Maintains global state, runs tick loop, records history, applies policy effects. |
| Agent Population    | Agent class (×N)                      | Individual agents with all attributes. Runs decision queue. Updates own state.   |
| Action Engine       | Action functions                      | One function per action. Pure side-effect model - modifies agent/world state.    |
| Visualisation       | Matplotlib + Seaborn                  | 6-panel live dashboard. Policy markers on all time-series charts.                |

## **10.2 Tech Stack**

| **Purpose**           | **Tool**                        | **Notes**                                      |
| --------------------- | ------------------------------- | ---------------------------------------------- |
| Core simulation       | Python 3.9+                     | Agent class, World class, action functions     |
| Numerical computation | NumPy                           | Vectorised need computations, history arrays   |
| Visualisation         | Matplotlib + Seaborn            | Animated grid, time-series charts, heatmaps    |
| LLM policy evaluation | Anthropic API (claude-sonnet-4) | JSON-structured impact evaluation              |
| Notebook environment  | Jupyter (.ipynb)                | Cell-by-cell execution, markdown documentation |
| Data storage          | JSON / pickle                   | Save/load simulation states                    |

## **10.3 Tick Loop**

| **Step**                 | **What Happens**                                                                                 |
| ------------------------ | ------------------------------------------------------------------------------------------------ |
| 1\. Environmental events | Random check: small chance of food_availability fluctuation each tick.                           |
| 2\. Need decay           | For every living agent: food, water, safety, social decay by base rate × environmental pressure. |
| 3\. Welfare application  | If welfare_enabled: unemployed agents receive welfare_amount.                                    |
| 4\. Emotion update       | Each agent: compute happiness, compute Unlust, update emotion state machine (with timer).        |
| 5\. Action selection     | Each agent: run decision priority queue, select one action.                                      |
| 6\. Action execution     | Execute selected action function. May modify agent and/or world state or other agents.           |
| 7\. Agent movement       | Each agent takes 1-2 random walk steps. Angry agents move more (restlessness).                   |
| 8\. Death check          | Any agent with food=0, water=0, or despair mortality check → alive = False.                      |
| 9\. World metrics update | Recompute crime_rate, protest_intensity, unemployment_rate from all living agents.               |
| 10\. History recording   | Append all metrics to history arrays for visualisation.                                          |

# **11\. Version Roadmap**

The project is designed in phases. Each version is a fully working simulation - later versions add complexity rather than fixing broken earlier ones.

## **v1 - Working Prototype (Current Scope)**

- Agent class with all v1 attributes
- 4 core needs: food, water, safety, social
- 5 emotions: happy, normal, sad, angry, despair
- Unlust engine
- Adler comparison on interaction
- 11 actions: work, buy_food, steal, protest, befriend, share, beg, harm_other, console, isolate, seek_job
- World class with environment state and history
- LLM policy evaluation with rule-based fallback
- 3 wealth classes, basic education, 10 job types
- 6-panel visualisation dashboard
- 5 policy experiments: baseline → tax → welfare → food crisis → recovery

## **v2 - Full Life Cycle**

- Full age lifecycle: child → young adult → middle aged → old → death
- Marriage and childbirth system
- Inheritance system
- Parents supporting children through education
- Old agents receiving support from children
- Sibling relationships and sibling jealousy (Adler sub-system)
- Sleep as explicit need with insomnia mechanic

## **v3 - Social Systems**

- Emergent community formation algorithm
- Inter-community tension and conflict
- Reputation propagation network (gossip chain - spreads imperfectly through friends)
- Organised crime gangs as group entities
- Therapist and doctor special job effects in full
- Rumour spreading as dominance action

## **v4 - Advanced Economy**

- White collar crime (low-morality rich agents)
- Invest action with compounding returns
- Business ownership as wealth tier above rich
- Labour market dynamics (supply/demand salary adjustment)
- Property market: price fluctuations based on crime and prosperity

## **v5 - Full Self-Actualisation**

- Purpose / meaning system for Layer 5 agents
- Creative professions unlocked by high creativity + purpose
- Community leadership roles (high reputation + morality)
- Political career track (high notoriety + ambition)
- Agent hobbies as mood modifiers (deferred to this stage)

## **v6 - UI & Scale**

- Interactive governance UI (not just notebook cells)
- Real-time animated visualisation (Pygame or web-based)
- Scale to 500-1000 agents
- Save/load simulation states with full history
- Policy suggestion mode: AI recommends interventions based on current world state

# **12\. Deliberately Deferred (Not Forgotten)**

These features were designed and discussed but deliberately excluded from v1 to keep the prototype buildable. They are documented here to avoid redesign work later.

| **Feature**                 | **Why Deferred**                                                 | **Target Version** |
| --------------------------- | ---------------------------------------------------------------- | ------------------ |
| Marriage & childbirth       | Too many edge cases for v1; entire lifecycle dependency chain    | v2                 |
| Age brackets                | Requires full lifecycle loop; children need parent tracking      | v2                 |
| Inheritance system          | Depends on age + marriage + family tracking                      | v2                 |
| Education cost from parents | Requires child-parent economic link                              | v2                 |
| Sibling relationships       | Requires birth tracking of same parents                          | v2                 |
| Community formation         | Requires sustained interaction history per pair                  | v3                 |
| Gossip/rumour network       | Requires friend graph with propagation delay                     | v3                 |
| Organised crime gangs       | Requires group entity class                                      | v3                 |
| White collar crime          | Requires investment tracking and audit system                    | v4                 |
| Agent hobbies               | Mood modifier - nice to have but not structurally important      | v5                 |
| Earthquakes/disasters       | Environment is neutral in current design by intention            | v5                 |
| Political career track      | Requires notoriety + ambition compound system                    | v5                 |
| Interactive UI              | Notebook is sufficient for prototype; UI is a presentation layer | v6                 |
| 500+ agents                 | Performance optimisation needed before scaling                   | v6                 |

# **13\. Configuration Constants Reference**

| **Constant**       | **Default Value** | **Effect of Increasing**                   | **Effect of Decreasing**                     |
| ------------------ | ----------------- | ------------------------------------------ | -------------------------------------------- |
| GRID_SIZE          | 20                | Agents more spread out, less interaction   | Denser, more interaction per tick            |
| N_AGENTS           | 80                | More diverse population, longer compute    | Faster but less statistically meaningful     |
| INTERACTION_RADIUS | 2                 | More agents interact each tick             | More isolated agents, slower social dynamics |
| FOOD_DECAY         | 0.018             | Agents need to buy food more often         | Longer survival without eating               |
| WATER_DECAY        | 0.014             | Faster water crisis                        | Slower water crisis                          |
| SAFETY_DECAY       | 0.004             | Safety degrades faster (more fear)         | Safety more stable baseline                  |
| SOCIAL_DECAY       | 0.009             | Agents get lonely faster                   | Social needs less urgent                     |
| HAPPY_THRESHOLD    | 0.65              | Harder to be happy (stricter gate)         | Easier to be happy                           |
| SAD_THRESHOLD      | 0.35              | Easier to fall into sadness                | More resilient against sadness               |
| ANGRY_UNLUST       | 0.58              | Slower anger escalation                    | Faster anger escalation (volatile world)     |
| DESPAIR_UNLUST     | 0.82              | Despair harder to reach                    | Despair easier to reach (harsher world)      |
| BASE_FOOD_COST     | 6.0               | Food is expensive - poor struggle more     | Food is cheap - poverty less deadly          |
| BASE_TAX_RATE      | 0.20              | More government revenue; less agent income | Less revenue; more take-home pay             |
| UNEMPLOYMENT_RATE  | 0.12              | More unemployment stress at start          | Near-full employment baseline                |

**End of Document - v1.0**

_This is a living document. Edit freely. Every section was derived from the original design conversation._
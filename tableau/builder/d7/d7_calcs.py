"""Every Who Leads Where (case study 7) calculation, in plain names.

The data source is the one Custom SQL, tableau/custom_sql_who_leads_where.sql: one row per row_type (Node, Tree,
Day, Signal, R1). The page reads the focus leader's numbers with FIXED expressions over the whole extract, so any
sheet can show them without a filter; the tree, calendar and lists filter to their own rows.
"""


def comma(x):
    """an integer below 1,000,000 with a thousands separator, as text"""
    return (f'(IF ISNULL({x}) THEN "" ELSEIF ABS({x}) >= 1000 THEN STR(INT({x} / 1000)) + "," + '
            f'RIGHT("00" + STR(INT({x}) % 1000), 3) ELSE STR(INT({x})) END)')


def pct1(num, den):
    return f'(IF ISNULL({den}) OR {den} = 0 THEN "0%" ELSE STR(ROUND(100 * {num} / {den}, 1)) + "%" END)'


def focus(field, wt='[p_Worker]', agg='MAX'):
    return f'{{FIXED : {agg}(IF [row_type] = "Node" AND [leader_id] = [p_Focus] AND [worker_type] = {wt} THEN [{field}] END)}}'


def focus_day(field):
    return (f'{{FIXED : MAX(IF [row_type] = "Day" AND [leader_id] = [p_Focus] AND [worker_type] = [p_Worker] '
            f'AND [day_offset] = [p_Day] THEN [{field}] END)}}')


def node(field, wt='[p_Worker]'):
    return f'{{FIXED [leader_id] : MAX(IF [row_type] = "Node" AND [worker_type] = {wt} THEN [{field}] END)}}'


def crumb(level, what):
    in_path = f'[row_type] = "Node" AND [worker_type] = "All" AND [leader_level] = "{level}" AND CONTAINS([F Path], "|" + [leader_id] + "|")'
    if level == 'L0':
        in_path += ' AND [depth_from_top] = [Crumb L0 Depth]'
    return f'{{FIXED : MAX(IF {in_path} THEN [{what}] END)}}'


SIGNALS = [  # code, short name (the panel), line, when it shows, good partner to ask
    ('S1', 'Budgeted in another org', 'Solid line',
     "Reports to this leader while their department sits in another leader's organization, often after a reorganization or a manager change.",
     'HR partner, Finance'),
    ('S2', 'Role from another function', 'Solid line',
     'The job family is one another function usually hires, such as a Product role in Commercial.', 'HR partner'),
    ('M1', 'Country leader for another country', 'Matrix line',
     "The person's country matrix does not cover the country they sit in, often after an international move.",
     'Matrix administrator'),
    ('M2', 'In two country matrices, or none', 'Matrix line', 'The design expects one country matrix per person.',
     'Matrix administrator'),
    ('M3', 'Matrix inactive or without a leader', 'Matrix line',
     "The matrix org has ended (Southern Europe split into Iberia and France), or its leader seat is open.",
     'Matrix administrator'),
    ('R1', 'Still naming a former leader', 'Role assignments',
     'A role assignment for an org unit still names the leader who held it before a leadership change.', 'HR Operations'),
]


def all_calcs():
    c = []
    a = lambda n, f: c.append((n, f))
    # ------------------------------------------------------------------ constants and switches
    a('zzTrue', 'TRUE')
    a('zzFalse', 'FALSE')
    a('Close Panel', 'FALSE')
    a('Empty Text', '""')
    a('Dynamic Text', '"Dynamic"')
    a('Theme Key', 'IF [p_Dark] THEN "_d" ELSE "_l" END')
    a('Show Light', 'NOT [p_Dark]')
    a('Show Dark', '[p_Dark]')
    for th, cond in (('Light', 'NOT [p_Dark]'), ('Dark', '[p_Dark]')):
        a(f'Show {th} Narrow', f'{cond} AND NOT [p_Zoom]')
        a(f'Show {th} Wide', f'{cond} AND [p_Zoom]')
        a(f'Show {th} Pick', f'{cond} AND [p_PickOpen]')
        a(f'Show {th} Cal', f'{cond} AND [p_CalOpen]')
        a(f'Show {th} Rules', f'{cond} AND [p_RulesOpen]')
    a('Toggle Zoom', 'NOT [p_Zoom]')
    a('Toggle Pick', 'NOT [p_PickOpen]')
    a('Toggle Cal', 'NOT [p_CalOpen]')
    a('Toggle Rules', 'NOT [p_RulesOpen]')
    a('WT Match', '[p_Worker] = "All" OR [worker_type] = [p_Worker]')
    a('Worker Words', 'CASE [p_Worker] WHEN "Employees" THEN "employees" WHEN "Contingent" THEN "contingent workers" ELSE "people" END')
    a('CEO ID', '{FIXED : MAX(IF [row_type] = "Node" AND [leader_level] = "L0" AND ISNULL([parent_leader_id]) THEN [leader_id] END)}')
    a('Report Label', '{FIXED : MAX([report_as_of_label])}')
    a('Report Date', '{FIXED : MAX([as_of_date])}')
    # ------------------------------------------------------------------ the focus leader
    for n, f in (('F People', 'people'), ('F Directs', 'directs'), ('F Indirects', 'indirects'), ('F Countries', 'countries'),
                 ('F Layers', 'layers_below'), ('F Median Span', 'median_span'), ('F Mgr 15', 'managers_15_plus'),
                 ('F Mgr One', 'managers_one_direct'), ('F Gaps', 'gap_people'), ('F Solid Gaps', 'solid_line_gap_people'),
                 ('F Matrix Gaps', 'matrix_gap_people'), ('F Managers Below', 'managers_below')):
        a(n, focus(f))
    for n, f in (('F Name', 'leader_name'), ('F Title', 'job_title'), ('F Level', 'leader_level'), ('F Path', 'path'),
                 ('F Parent', 'parent_leader_id'), ('F Parent Name', 'parent_leader_name'), ('F Function', 'function_name'),
                 ('F Depth', 'depth_from_top'), ('F Child Leaders', 'child_leaders'), ('F R1', 'assignments_naming_former_leader'),
                 ('F Office', 'office_name'), ('F Country', 'country_name')):
        a(n, focus(f, '"All"'))
    for n, f in (('F Day People', 'people'), ('F Day At Work', 'at_work'), ('F Day Off', 'off'), ('F Day Off PTO', 'off_time_off'),
                 ('F Day Off Leave', 'off_leave'), ('F Day Off Holiday', 'off_public_holiday'), ('F Day Left', 'left_team')):
        a(n, focus_day(f))
    a('Day Date', '{FIXED : MAX(IF [row_type] = "Day" AND [day_offset] = [p_Day] THEN [day] END)}')
    a('Day Weekend', '{FIXED : MAX(IF [row_type] = "Day" AND [day_offset] = [p_Day] AND [is_weekend] THEN 1 ELSE 0 END)}')
    a('Day Text', 'LEFT(DATENAME("weekday", [Day Date]), 3) + ", " + LEFT(DATENAME("month", [Day Date]), 3) + " " + STR(DAY([Day Date]))')
    a('Day Lead', 'IF [p_Day] = 0 THEN "Today · " + [Day Text] ELSE [Day Text] END')
    a('Report Short', 'LEFT(DATENAME("weekday", [Report Date]), 3) + ", " + [Report Label]')
    # ------------------------------------------------------------------ headline and KPIs
    a('F People Txt', comma('[F People]'))
    a('F Gaps Txt', comma('[F Gaps]'))
    a('F Gap Pct Txt', pct1('[F Gaps]', '[F People]'))
    a('F Countries Txt', 'STR([F Countries]) + IF [F Countries] = 1 THEN " country" ELSE " countries" END')
    a('Head Eyebrow', 'UPPER([F Name] + " · " + [F Level] + " · " + [F Title] + " · as of " + [Report Label])')
    a('Head Leads', '[F Name] + " leads "')
    a('Head People', '[F People Txt] + " " + [Worker Words]')
    a('Head In', '" in " + [F Countries Txt] + ". "')
    a('Head Gaps', '[F Gaps Txt] + " (" + [F Gap Pct Txt] + ")"')
    a('Head Tail', 'IF [F Gaps] = 1 THEN " shows an alignment gap." ELSE " show an alignment gap." END')
    a('K1 Value', '[F People Txt]')
    a('K1 Note', comma('[F Directs]') + ' + " directs · " + ' + comma('[F Indirects]') + ' + " indirect"')
    a('K2 Value', 'IF [Day Weekend] = 1 THEN "Weekend" ELSE ' + comma('[F Day At Work]').replace('IF ISNULL', '(IF ISNULL', 1) + ') END')
    a('K2 Note', 'IF [Day Weekend] = 1 THEN [Day Text] + " · nobody is scheduled" ELSE ' + comma('[F Day Off]').replace('IF ISNULL', '(IF ISNULL', 1)
      + ') + " off · " + IF [p_Day] = 0 THEN "today" ELSE [Day Text] END END')
    a('K3 Value', 'STR([F Layers])')
    a('K3 Note', 'IF [F Depth] = 0 THEN "The whole company" ELSEIF [F Depth] = 1 THEN "1 below the CEO" ELSE STR([F Depth]) + " below the CEO" END')
    a('K4 Value', 'IF ISNULL([F Median Span]) THEN "–" ELSEIF [F Median Span] = INT([F Median Span]) THEN STR(INT([F Median Span])) '
      'ELSE STR(ROUND([F Median Span], 1)) END')
    a('K4 Note', 'STR([F Mgr 15]) + " lead 15+ · " + STR([F Mgr One]) + " lead one"')
    a('K5 Value', '[F Gaps Txt]')
    a('K5 Note', '[F Gap Pct Txt] + " of " + [Worker Words] + " · " + ' + comma('[F Matrix Gaps]') + ' + " matrix"')
    # ------------------------------------------------------------------ the path (rail and breadcrumb)
    a('Crumb L0 Depth', '{FIXED : MAX(IF [row_type] = "Node" AND [worker_type] = "All" AND [leader_level] = "L0" '
      'AND CONTAINS([F Path], "|" + [leader_id] + "|") THEN [depth_from_top] END)}')
    for lv in ('L0', 'L1', 'L2'):
        a(f'Crumb {lv}', crumb(lv, 'leader_name'))
        a(f'Crumb {lv} ID', crumb(lv, 'leader_id'))
    a('Org L0 Text', 'IFNULL([Crumb L0], "–")')
    a('Org L1 Text', 'IFNULL([Crumb L1], IF [F Level] = "L0" THEN "All " + STR([F Child Leaders]) + " leaders" ELSE "–" END)')
    a('Org L2 Text', 'IFNULL([Crumb L2], IF [F Level] = "L1" THEN "All " + STR([F Child Leaders]) + " leaders" ELSE "–" END)')
    a('Org Below Text', 'IF [F Level] = "Manager" THEN "› " + [F Name] ELSE "" END')
    a('Pick B0 Default', 'IFNULL([Crumb L0 ID], [CEO ID])')
    a('Pick B1 Default', 'IFNULL([Crumb L1 ID], "")')
    a('Crumb Chain', 'IFNULL([Crumb L0] + " (L0)", "") + IF ISNULL([Crumb L1]) THEN "" ELSE " › " + [Crumb L1] + " (L1)" END '
      '+ IF ISNULL([Crumb L2]) THEN "" ELSE " › " + [Crumb L2] + " (L2)" END + IF [F Level] = "Manager" THEN " › " + [F Name] ELSE "" END')
    a('Tree Hint', 'IF [p_Tree] = "Dynamic" THEN "Dynamic · the chain from the top to " + [F Name] + ", and their team · '
      'click anyone above to go back up" ELSE "Static · three levels of leaders below " + [F Name] + " at once · click a circle to open it" END')
    # ------------------------------------------------------------------ the tree
    # Dynamic is ONE tree for the whole company (tier = depth below the CEO). A circle shows when its manager is on the
    # focus leader's path (F Path lists the CEO down to the focus, the focus included), so the page shows the chain from
    # the top, every level's leaders, and the focus's own team. Nothing in the layout moves, so Tableau animates a click.
    # Four rows at most: two levels above the focus, the focus's row and their team; a link shows only when its upper
    # circle is on the page too, except its points 15 and 16 (the gap halves of the circle's pie, under the circle).
    # p_Path holds the focus's path and is set by the same click as p_Focus, so these are plain row tests: inside the
    # context filter, a FIXED lookup of the path would run again inside every FIXED read of the tree
    a('On Path', 'CONTAINS([p_Path], "|" + [node_id] + "|")')
    a('Parent On Path', 'ISNULL([parent_node_id]) OR CONTAINS([p_Path], "|" + [parent_node_id] + "|")')
    # the path a tree click sets: the clicked leader's, or in Static, the focus circle's manager's (it goes up one)
    a('Path Target', 'IF [tree_mode] = "Static" AND [tier] = 0 AND NOT ISNULL([N Parent]) '
      'THEN LEFT([path], LEN([path]) - LEN([node_id]) - 1) ELSE [path] END')
    a('In Team', 'IFNULL([parent_node_id] = [p_Focus], FALSE)')
    a('In Tree View', '[row_type] = "Tree" AND [tree_mode] = [p_Tree] AND ('
      '([tree_mode] = "Static" AND [focus_leader_id] = [p_Focus]) '
      'OR ([tree_mode] = "Dynamic" AND [Parent On Path] AND [tier] >= [F Depth] - 2 + IIF([mark_type] = "Link" AND [point_index] < 15, 1, 0)))')
    for n, f in (('N People', 'people'), ('N Gaps', 'gap_people'), ('N Directs', 'directs'), ('N Indirects', 'indirects'),
                 ('N Countries', 'countries')):
        a(n, node(f))
    a('N Parent', node('parent_leader_id', '"All"'))
    a('N Parent Name', node('parent_leader_name', '"All"'))
    a('N At Work', '{FIXED [leader_id] : MAX(IF [row_type] = "Day" AND [worker_type] = [p_Worker] AND [day_offset] = [p_Day] THEN [at_work] END)}')
    a('N Shown', 'IF [p_Count] = "At work" AND [Day Weekend] = 0 THEN [N At Work] ELSE [N People] END')
    a('N Shown Txt', comma('[N Shown]') + ' + IF [p_Count] = "At work" AND [Day Weekend] = 0 THEN " at work" ELSE "" END')
    a('Y Link', 'IF [mark_type] = "Link" THEN -[y] END')
    # Each pie is three wedges: half the gap slice (a link's point 15), the people without a gap (the Node row), and the
    # other half (point 16). Tableau labels a wedge at its middle angle, so splitting the gap around 12 o'clock centers
    # the big wedge, and its name label, on 6 o'clock: straight below the circle.
    a('Node Y', '{FIXED [tree_mode], [focus_leader_id], [node_id] : MIN(IF [mark_type] = "Node" THEN [y] END)}')
    a('Node X', '{FIXED [tree_mode], [focus_leader_id], [node_id] : MIN(IF [mark_type] = "Node" THEN [x] END)}')
    # the x of every mark: point 15 of a link sits on its circle's center, so its gap half joins the circle's pie (a few
    # pixels off and Tableau would draw a second pie on top); the link's last stretch runs under the circle anyway
    a('X Plot', 'IF [mark_type] = "Link" AND [point_index] = 15 THEN [Node X] ELSE [x] END')
    a('Y Node', 'IF [mark_type] = "Node" OR [point_index] = 16 THEN -[y] ELSEIF [point_index] = 15 THEN -[Node Y] END')
    a('Wedge Order', 'IF [mark_type] = "Node" THEN 2 ELSEIF [point_index] = 15 THEN 1 ELSE 3 END')
    a('Pie Angle', 'IF [mark_type] = "Node" THEN [N People] - [N Gaps] ELSEIF [point_index] >= 15 THEN [N Gaps] / 2 END')
    a('Pie Size', 'IF [tree_mode] = "Static" AND [tier] = 3 THEN 1 ELSEIF [tree_mode] = "Static" AND [tier] = 2 THEN [N People] * 0.35 '
      'ELSEIF [tree_mode] = "Dynamic" AND NOT [On Path] AND NOT [In Team] THEN [N People] * 0.35 ELSE [N People] END')
    a('Row Count', 'IIF(ISNULL([row_type]), 1, 1)')
    a('Pie Color', '(IF [mark_type] <> "Node" AND [point_index] < 15 THEN "none" ELSEIF [mark_type] <> "Node" THEN "gap" '
      'ELSEIF [node_id] = [p_Focus] THEN "focus" ELSEIF [tree_mode] = "Dynamic" AND [On Path] THEN "open" ELSE "node" END) + [Theme Key]')
    a('Link Kind', '(IF [tree_mode] = "Dynamic" AND ([On Path] OR [In Team]) THEN "sel" ELSE "link" END) + [Theme Key]')
    # labels: the path and the focus's team in Dynamic (the other leaders of each level stay small and quiet: hover names
    # them); tiers 0 and 1 in Static
    a('Show Label', '[mark_type] = "Node" AND IIF([tree_mode] = "Static", [tier] < 2, [On Path] OR [In Team])')
    # a team of more than four is one unit apart: every other label drops two lines, so neighbors never collide
    a('Label Drop', 'IF [tree_mode] = "Dynamic" AND [In Team] AND [slots] > 4 AND [slot] % 2 = 1 THEN CHAR(10) + CHAR(10) ELSE "" END')
    a('Node Label Name', 'IF NOT [Show Label] THEN "" ELSEIF [node_id] = [p_Focus] THEN [leader_name] '
      'ELSE [Label Drop] + SPLIT([leader_name], " ", -1) END')
    a('Node Label Count', 'IF NOT [Show Label] THEN "" ELSE [N Shown Txt] END')
    a('Focus Target', 'IF [tree_mode] = "Static" AND [tier] = 0 THEN IFNULL([N Parent], [node_id]) ELSE [node_id] END')
    a('Tip Action', 'IF [node_id] = [p_Focus] THEN (IF ISNULL([N Parent]) THEN "The top of Arcadia" '
      'ELSEIF [tree_mode] = "Static" THEN "Click to go up to " + [N Parent Name] ELSE "Open now: click anyone above to go back up" END) '
      'ELSEIF [tree_mode] = "Dynamic" AND [On Path] THEN "Click to go back up to " + [leader_name] '
      'ELSE "Click to open their organization" END')
    a('Tip People', comma('[N People]') + ' + " " + [Worker Words] + " · " + ' + comma('[N Directs]') + ' + " directs, " + '
      + comma('[N Indirects]') + ' + " indirect · " + STR([N Countries]) + " countries"')
    a('Tip Gaps', comma('[N Gaps]') + ' + " with an alignment gap (" + ' + pct1('[N Gaps]', '[N People]') + ' + ")"')
    a('Tip At Work', 'IF [Day Weekend] = 1 THEN [Day Text] + " is a weekend" ELSE ' + comma('[N At Work]').replace('IF ISNULL', '(IF ISNULL', 1)
      + ') + " at work on " + [Day Text] END')
    # ------------------------------------------------------------------ toggles
    # the Count, Tree and Theme toggles draw two segments from the focus leader's All and Employees rows (Node rows sit in
    # every sheet's context), so Seg Mode stands in for a two-value field
    a('Seg Row', '[row_type] = "Node" AND [leader_id] = [p_Focus] AND ([worker_type] = "All" OR [worker_type] = "Employees")')
    a('Seg Mode', 'IF [worker_type] = "All" THEN "Dynamic" ELSE "Static" END')
    a('Seg Key', 'IF [Seg Mode] = "Dynamic" THEN 1 ELSE 2 END')
    a('Count Option', 'IF [Seg Mode] = "Dynamic" THEN "Everyone" ELSE "At work" END')
    a('Count Shape', '"d7_count_" + (IF [Seg Mode] = "Dynamic" THEN "everyone" ELSE "atwork" END) + "_" '
      '+ (IF [Count Option] = [p_Count] THEN "on" ELSE "off" END) + [Theme Key]')
    a('Tree Shape', '"d7_tree_" + LOWER([Seg Mode]) + "_" + (IF [Seg Mode] = [p_Tree] THEN "on" ELSE "off" END) + [Theme Key]')
    a('Theme Is Dark', '[Seg Mode] = "Static"')
    a('Theme Shape', '"d7_theme_" + (IF [Seg Mode] = "Dynamic" THEN "light" ELSE "dark" END) + "_" '
      '+ (IF [Theme Is Dark] = [p_Dark] THEN "on" ELSE "off" END) + [Theme Key]')
    a('Worker Row', '[row_type] = "Node" AND [leader_id] = [p_Focus]')
    a('Worker Key', 'CASE [worker_type] WHEN "All" THEN 1 WHEN "Employees" THEN 2 ELSE 3 END')
    a('Worker Shape', '"d7_worker_" + LOWER([worker_type]) + "_" + (IF [worker_type] = [p_Worker] THEN "on" ELSE "off" END) + [Theme Key]')
    a('Focus Row', '[row_type] = "Node" AND [leader_id] = [p_Focus] AND [worker_type] = "All"')
    a('Zoom Shape', '(IF [p_Zoom] THEN "d7_collapse" ELSE "d7_expand" END) + [Theme Key]')
    a('Info Shape', '"d7_info" + [Theme Key]')
    a('Close Shape', '"d7_close" + [Theme Key]')
    a('GitHub Shape', '"d7_github" + [Theme Key]')
    a('LinkedIn Shape', '"d7_linkedin" + [Theme Key]')
    # ------------------------------------------------------------------ the leader picker
    a('Pick Base', '[row_type] = "Node" AND [worker_type] = "All"')
    a('Pick Row L0', '[Pick Base] AND [leader_level] = "L0"')
    a('Pick Row L1', '[Pick Base] AND [leader_level] = "L1" AND [parent_leader_id] = [p_B0]')
    a('Pick Row L2', '[Pick Base] AND [leader_level] = "L2" AND [parent_leader_id] = [p_B1]')
    a('Pick Rank', '1000000 - [people]')
    a('Pick Shape', '(IF CONTAINS([F Path], "|" + [leader_id] + "|") THEN "d7_dot_on" ELSE "d7_dot_off" END) + [Theme Key]')
    a('Pick Sub', '[job_title] + " · " + ' + comma('[people]'))
    a('Tick X', 'MIN(0.5)')
    a('Pick People', comma('[people]'))
    a('B0 Name', '{FIXED : MAX(IF [Pick Base] AND [leader_id] = [p_B0] THEN [leader_name] END)}')
    a('B1 Name', '{FIXED : MAX(IF [Pick Base] AND [leader_id] = [p_B1] THEN [leader_name] END)}')
    a('Pick Head L1', 'IF ISNULL([B0 Name]) THEN "L1" ELSE "L1 · UNDER " + UPPER([B0 Name]) END')
    a('Pick Head L2', 'IF ISNULL([B1 Name]) THEN "L2 · PICK AN L1 LEADER" ELSE "L2 · UNDER " + UPPER([B1 Name]) END')
    # ------------------------------------------------------------------ the calendar
    a('Cal Row', '[row_type] = "Day" AND [leader_id] = [p_Focus] AND [worker_type] = [p_Worker]')
    a('Report Monday', 'DATEADD("day", 1 - DATEPART("iso-weekday", [Report Date]), [Report Date])')
    a('Cal DOW', 'DATEPART("iso-weekday", [day])')
    a('Cal Week', 'DIV(DATEDIFF("day", [Report Monday], [day]), 7)')
    a('Cal Pos', '1')
    a('Cal Kind', '(IF [is_weekend] THEN "we" ELSEIF [day_offset] = [p_Day] THEN "sel" '
      'ELSEIF [off] >= 0.12 * [people] THEN "high" ELSE "low" END) + [Theme Key]')
    a('Cal Day Label', 'IF [day_offset] = 0 OR DAY([day]) = 1 THEN LEFT(DATENAME("month", [day]), 3) + " " + STR(DAY([day])) ELSE STR(DAY([day])) END')
    a('Cal Value', 'IF [is_weekend] THEN "Weekend" ELSE ' + comma('[at_work]').replace('IF ISNULL', '(IF ISNULL', 1) + ') END')
    a('Cal Off', 'IF [is_weekend] THEN "" ELSE ' + comma('[off]').replace('IF ISNULL', '(IF ISNULL', 1) + ') + " off" END')
    a('Cal Tip', 'LEFT(DATENAME("weekday", [day]), 3) + ", " + LEFT(DATENAME("month", [day]), 3) + " " + STR(DAY([day]))')
    a('Quiet At Work', '{FIXED : MIN(IF [row_type] = "Day" AND [leader_id] = [p_Focus] AND [worker_type] = [p_Worker] AND NOT [is_weekend] THEN [at_work] END)}')
    a('Quiet Date', '{FIXED : MIN(IF [row_type] = "Day" AND [leader_id] = [p_Focus] AND [worker_type] = [p_Worker] AND NOT [is_weekend] '
      'AND [at_work] = [Quiet At Work] THEN [day] END)}')
    a('Quiet Text', '"The quietest weekday is " + LEFT(DATENAME("weekday", [Quiet Date]), 3) + ", " + LEFT(DATENAME("month", [Quiet Date]), 3) '
      '+ " " + STR(DAY([Quiet Date])) + ": " + ' + comma('[Quiet At Work]') + ' + " at work."')
    a('Left Text', 'IF [F Day Left] > 0 THEN "By " + [Day Text] + ", " + ' + comma('[F Day Left]')
      + ' + " of today\'s people have left the team: mostly contingent assignments ending with no extension on file yet." ELSE "" END')
    a('Cal Title', '"Who is at work · " + [F Name] + "\'s organization"')
    a('Cal Field Value', 'IF [Day Weekend] = 1 THEN "Weekend" ELSE ' + comma('[F Day At Work]').replace('IF ISNULL', '(IF ISNULL', 1)
      + ') + " of " + ' + comma('[F Day People]') + ' END')
    a('Cal Field Note', 'IF [Day Weekend] = 1 THEN "Pick a weekday" ELSE ' + comma('[F Day Off]').replace('IF ISNULL', '(IF ISNULL', 1)
      + ') + " off: PTO, leave or a holiday" END')
    # ------------------------------------------------------------------ the alignment panel
    a('Sig Scaffold', '([row_type] = "Signal" OR [row_type] = "R1") AND [leader_id] = [CEO ID]')
    a('Sig Order', 'CASE [signal_code] ' + ' '.join(f'WHEN "{s[0]}" THEN {i}' for i, s in enumerate(SIGNALS, 1)) + ' END')
    a('Sig Count', '{FIXED [signal_code] : COUNTD(IF ([row_type] = "Signal" OR [row_type] = "R1") AND [leader_id] = [p_Focus] '
      'AND [WT Match] THEN [person_id] END)}')
    a('Sig Max', '{FIXED : MAX([Sig Count])}')
    a('Sig Bar Len', 'IF [Sig Max] > 0 AND [Sig Count] > 0 THEN MAX(1, INT(ROUND(30 * [Sig Count] / [Sig Max], 0))) ELSE 0 END')
    a('Sig Bar', 'REPLACE(SPACE([Sig Bar Len]), " ", "━")')
    a('Sig Track', 'REPLACE(SPACE(30 - [Sig Bar Len]), " ", "━")')
    a('Sig Count Txt', comma('[Sig Count]'))
    a('Sig Rule', 'CASE [signal_code] ' + ' '.join(f'WHEN "{s[0]}" THEN "{s[3]}"' for s in SIGNALS) + ' END')
    a('Sig Partner', 'CASE [signal_code] ' + ' '.join(f'WHEN "{s[0]}" THEN "{s[4]}"' for s in SIGNALS) + ' END')
    a('Is Solid', '[signal_line] = "Solid line"')
    a('Is Matrix', '[signal_line] = "Matrix line"')
    a('Is Role', '[signal_line] = "Role assignments"')
    a('Solid Total', comma('[F Solid Gaps]') + ' + " PEOPLE"')
    a('Matrix Total', comma('[F Matrix Gaps]') + ' + " PEOPLE"')
    a('Role Total', 'STR([F R1]) + IF [F R1] = 1 THEN " ASSIGNMENT" ELSE " ASSIGNMENTS" END')
    # ------------------------------------------------------------------ context: each sheet reads only the rows it needs
    # A context filter runs before every FIXED expression, so the page's many FIXED reads scan a small slice of the
    # 580,222 rows instead of all of them.
    a('Ctx Leaders', '[row_type] = "Node" OR [row_type] = "Signal" OR [row_type] = "R1"')
    a('Ctx Days', '[row_type] = "Day" AND [leader_id] = [p_Focus] AND [worker_type] = [p_Worker]')
    # the company tree enters the context only where its manager is on the focus's path: a few hundred rows of 63,091
    a('Ctx Tree', '([row_type] = "Tree" AND [tree_mode] = [p_Tree] AND IIF([tree_mode] = "Dynamic", [Parent On Path], [focus_leader_id] = [p_Focus])) '
      'OR ([row_type] = "Node" AND ([worker_type] = [p_Worker] OR [worker_type] = "All")) '
      'OR ([row_type] = "Day" AND [worker_type] = [p_Worker] AND [day_offset] = [p_Day])')
    a('Rail As Of', '"Synthetic data as of " + [Report Label]')
    return c


DTYPES = {'Cal DOW': 'integer', 'Cal Week': 'integer', 'Seg Key': 'integer', 'Worker Key': 'integer', 'Sig Order': 'integer',
          'Pick Rank': 'integer', 'Day Weekend': 'integer', 'Sig Bar Len': 'integer', 'Cal Pos': 'integer', 'F Depth': 'integer',
          'F Child Leaders': 'integer', 'F R1': 'integer', 'Report Monday': 'date', 'Quiet Date': 'date', 'Day Date': 'date',
          'Report Date': 'date', 'Pie Angle': 'real', 'Wedge Order': 'integer', 'Node Y': 'real', 'Node X': 'real', 'X Plot': 'real', 'Pie Size': 'real',
          # IFNULL() takes the type of its arguments; the writer cannot infer it, so these are named here
          'Org L0 Text': 'string', 'Org L1 Text': 'string', 'Org L2 Text': 'string', 'Pick B0 Default': 'string',
          'Pick B1 Default': 'string', 'Focus Target': 'string', 'Path Target': 'string', 'Seg Mode': 'string'}
ROLES = {'Cal DOW': ('dimension', 'ordinal'), 'Cal Week': ('dimension', 'ordinal'), 'Seg Key': ('dimension', 'ordinal'),
         'Worker Key': ('dimension', 'ordinal'), 'Sig Order': ('dimension', 'ordinal'), 'Pick Rank': ('dimension', 'ordinal'), 'Wedge Order': ('dimension', 'ordinal')}

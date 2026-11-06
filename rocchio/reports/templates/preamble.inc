\documentclass[10pt]{article}
\usepackage[letterpaper,margin=0.85in,top=0.9in,bottom=0.85in]{geometry}
\usepackage[T1]{fontenc}\usepackage[scaled=0.92]{helvet}\renewcommand{\familydefault}{\sfdefault}\usepackage{microtype}
\usepackage{sansmath}\sansmath\usepackage{amsmath,tabularx,array,enumitem,titlesec,listings,float,graphicx,fancyhdr,ragged2e}
\usepackage[table]{xcolor}
\usepackage[most]{tcolorbox}\tcbuselibrary{raster}
\definecolor{navy}{HTML}{12355B}\definecolor{teal}{HTML}{0F766E}\definecolor{tealtint}{HTML}{E6F4F1}
\definecolor{amber}{HTML}{C2570C}\definecolor{ambertint}{HTML}{FDF0E3}\definecolor{zebra}{HTML}{F1F5F9}
\definecolor{ink}{HTML}{1E293B}\definecolor{muted}{HTML}{64748B}\definecolor{termbg}{HTML}{0F172A}\definecolor{termfg}{HTML}{E2E8F0}
\usepackage[colorlinks=true,urlcolor=teal,linkcolor=navy,citecolor=navy]{hyperref}
\usepackage{url}\def\UrlBreaks{\do\/\do-\do_\do.\do=}
\usepackage[font={small,color=ink},labelfont={bf,color=teal},skip=4pt]{caption}
\color{ink}
\setlength{\parskip}{5pt}\setlength{\parindent}{0pt}\tolerance=1500\emergencystretch=1.5em
\titleformat{\section}[block]{\bfseries\large\color{navy}}{\colorbox{teal}{\textcolor{white}{\thesection}}}{.6em}{}[{\color{teal}\titlerule[1.2pt]}]
\titlespacing*{\section}{0pt}{14pt}{6pt}
\setlist{nosep,leftmargin=1.4em,topsep=2pt,label=\textcolor{teal}{\textbullet}}
\setlength{\tabcolsep}{5pt}\renewcommand{\arraystretch}{1.18}\arrayrulecolor{navy}
\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}\renewcommand{\footrulewidth}{0pt}
\fancyfoot[L]{\footnotesize\textcolor{muted}{CSC 618 Information Retrieval}}\fancyfoot[R]{\footnotesize\textcolor{teal}{\bfseries\thepage}}
\lstdefinestyle{term}{basicstyle=\ttfamily\scriptsize\color{termfg},backgroundcolor=\color{termbg},breaklines=true,columns=fullflexible,keepspaces=true,frame=single,rulecolor=\color{termbg},framesep=6pt,xleftmargin=6pt,xrightmargin=6pt,showstringspaces=false}
\lstdefinestyle{code}{basicstyle=\ttfamily\scriptsize\color{ink},backgroundcolor=\color{zebra},keywordstyle=\color{teal}\bfseries,commentstyle=\color{muted}\itshape,stringstyle=\color{amber},breaklines=true,columns=fullflexible,keepspaces=true,frame=leftline,rulecolor=\color{teal},framerule=2pt,showstringspaces=false,upquote=true}
\lstset{style=code}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\newcommand{\q}[1]{\par\medskip\begin{tcolorbox}[enhanced,colback=ambertint,colframe=ambertint,borderline west={3pt}{0pt}{amber},sharp corners,boxrule=0pt,left=8pt,top=3pt,bottom=3pt,before skip=4pt,after skip=4pt]\textbf{\textcolor{navy}{#1}}\end{tcolorbox}\par}
\newcommand{\stat}[3]{\begin{tcolorbox}[colback=#3,colframe=#3,coltext=white,arc=4pt,boxrule=0pt,left=6pt,right=6pt,top=5pt,bottom=5pt,halign=center]{\footnotesize #1}\\[2pt]{\normalsize\bfseries #2}\end{tcolorbox}}
\newtcolorbox{note}{enhanced,colback=tealtint,colframe=tealtint,borderline west={3pt}{0pt}{teal},sharp corners,boxrule=0pt,left=8pt,top=4pt,bottom=4pt,before skip=6pt,after skip=6pt}

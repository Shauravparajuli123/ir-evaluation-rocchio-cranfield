\documentclass[10pt]{article}
\usepackage[letterpaper,margin=0.9in]{geometry}
\usepackage[T1]{fontenc}\usepackage{mathptmx}\usepackage{courier}\usepackage{microtype}
\usepackage{amsmath,booktabs,tabularx,array,enumitem,titlesec,listings,float}
\usepackage{xcolor}
\usepackage[colorlinks=true,urlcolor=blue!55!black,linkcolor=black,citecolor=black]{hyperref}
\usepackage{url}\def\UrlBreaks{\do\/\do-\do_\do.\do=}
\usepackage[font=small,labelfont=bf,skip=3pt]{caption}
\setlength{\parskip}{4pt}\setlength{\parindent}{0pt}\tolerance=1500\emergencystretch=1.5em
\titleformat{\section}{\normalfont\bfseries\normalsize}{\thesection.}{0.4em}{}
\titlespacing*{\section}{0pt}{10pt}{3pt}
\setlist{nosep,leftmargin=1.4em,topsep=2pt}
\setlength{\tabcolsep}{4pt}
\lstset{basicstyle=\ttfamily\scriptsize,breaklines=true,columns=fullflexible,keepspaces=true,frame=single,framerule=0.3pt,rulecolor=\color{black!40},showstringspaces=false,upquote=true}
\newcommand{\docheader}[1]{\begin{center}{\small Utica University \textbar{} Department of Computer Science \textbar{} Fall 2026}\\[1pt]{\small CSC 618: Information Retrieval \textbar{} Week 10 Assignment}\\[5pt]{\large\bfseries #1}\\[3pt]{\small November 2026}\end{center}\vspace{-2pt}}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\newcommand{\q}[1]{\par\medskip\textit{#1}\par}

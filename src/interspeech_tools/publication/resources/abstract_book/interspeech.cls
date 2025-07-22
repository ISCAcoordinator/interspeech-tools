%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Class definition
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{INTERSPEECH2025_proceedings}[2025/01/06 Official Interspeech 2025 package]

\newif\if@print\@printfalse
\newif\if@abstract\@abstractfalse

\DeclareOption{onecolumn}{\OptionNotUsed}
\DeclareOption{print}{\@printtrue}
\DeclareOption{screen}{\@printfalse}
\DeclareOption{abstract}{\@abstracttrue}
\DeclareOption{noabstract}{\@abstractfalse}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{book}}
\ProcessOptions\relax

\LoadClass{book}

% TODO: to sort
\RequirePackage{hyperref}
\RequirePackage{multicol}
\RequirePackage{array}
% \newcolumntype{L}[1]{>{\raggedright\let\newline\\\arraybackslash\hspace{0pt}}m{#1}}
\newcolumntype{C}[1]{>{\centering\let\newline\\\arraybackslash\hspace{0pt}}m{#1}}
% \newcolumntype{R}[1]{>{\raggedleft\let\newline\\\arraybackslash\hspace{0pt}}m{#1}}

%%% }}}



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% General structure & formatting
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{


\RequirePackage{pdfpages}
% control margins & spacing
\RequirePackage{geometry}

% \geometry{
%     paperheight=303mm,
%     paperwidth=216mm,  % or: "paper=a4paper"
%     textheight=297mm,
%     textwidth=210mm,
%     margin=0pt,
%     includeheadfoot,
%     showframe=true,
%     showcrop=true
% }

\RequirePackage{setspace}
    \newlength{\footrectangleheight}

% Printing version or screen version
\if@print
    \RequirePackage{lscape}
    \setlength{\footrectangleheight}{15mm}
    \newcommand{\includeelements}[2][]{%
        \includepdf[#1,offset={0mm, 0mm}]{content-elements/print/#2}
    }

    \geometry{%
        paperwidth=216mm,
        paperheight=303mm,
        layoutvoffset=6mm,
        includeheadfoot,
        left=15mm,
        right=15mm,
        top=3mm,
        headheight=20mm, % as per the warning by fancyhdr
        bottom=15mm,
    }
\else

    \RequirePackage{pdflscape}
    \setlength{\footrectangleheight}{10mm}

    \geometry{%
        paperwidth=210mm,
        paperheight=297mm,
        left=15mm,
        right=15mm,
        top=40mm,
        headheight=20mm, % as per the warning by fancyhdr
        bottom=15mm,
    }

    \newcommand{\includeelements}[2][]{%
        \includepdf[#1]{content-elements/online/#2}
    }
\fi

% Font
\RequirePackage{lmodern}
\renewcommand{\sfdefault}{phv}
\renewcommand{\rmdefault}{ptm}
\renewcommand{\ttdefault}{pcr}
\renewcommand{\familydefault}{\sfdefault}

%%% }}}


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Table of Contents
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{

\RequirePackage{etoc}
\etocsettocstyle{\noindent\rule{\linewidth}{1.5pt}\vskip0.5\baselineskip}{\noindent\rule{\linewidth}{1.5pt}}
% Remove indentation and tweak spacing in local table of contents
\etocsetstyle{section}
  {} % before toc
  {} % after toc
  {\noindent\etocname\hfill\etocpage} % entry format: name + page number
  % {\noindent\etocskipfirstprefix} % for each entry
  {} % after each entry

%%% }}}


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Colours and theme
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{

\RequirePackage[table]{xcolor}
\RequirePackage[most]{tcolorbox}

\input{theme/colours.tex}

%% Header, footers and overall page format
\RequirePackage{lastpage}
\RequirePackage{fancyhdr}
\renewcommand{\headrulewidth}{0pt}

\fancypagestyle{fancy}{%
  \fancyhf{} % clear all header and footer fields
  \fancyhead[LE]{
      \begin{tikzpicture}[overlay, remember picture]%
          \node[anchor=north, inner sep=0,outer sep=0] at (current page.north){
              \IfFileExists{theme/standard_header_left.pdf}
              {\includegraphics[width=\paperwidth]{theme/standard_header_left.pdf}}
              {}
          };
      \end{tikzpicture}
  }
  \fancyhead[LO]{
      \begin{tikzpicture}[overlay, remember picture]%
          \node[anchor=north, inner sep=0,outer sep=0] at (current page.north){
              \IfFileExists{theme/standard_header_right.pdf}
              {\includegraphics[width=\paperwidth]{theme/standard_header_right.pdf}}
              {}
          };
      \end{tikzpicture}
  }
  \fancyfoot[C]{
      \begin{tikzpicture}[overlay, remember picture]%
          \fill[FooterBackgroundColour] (current page.south west)+(0,0) rectangle ($(current page.south east)+(,\footrectangleheight)$);
          \node[anchor=south, text=FooterForegroundColour, font=\large\bf, minimum size=\footrectangleheight] at (current page.south) {Page \thepage\ of \pageref*{LastPage}};
      \end{tikzpicture}
  }
}

\fancypagestyle{onlyfoot}{%
  \fancyhf{} % clear all header and footer fields
  \fancyfoot[C]{
      \begin{tikzpicture}[overlay, remember picture]%
          \fill[FooterBackgroundColour] (current page.south west)+(0mm,0) rectangle ($(current page.south east)+(0mm,\footrectangleheight)$);
          \node[anchor=south, text=FooterForegroundColour, font=\large\bf, minimum size=\footrectangleheight] at (current page.south) {Page \thepage\ of \pageref*{LastPage}};
      \end{tikzpicture}
  }
}

\fancypagestyle{plain}{%
  \fancyhf{} % clear all header and footer fields
}

% Graphics & Images
\RequirePackage{graphicx}
\RequirePackage{tikz} % Required for drawing custom shapes
\usetikzlibrary{shapes,shadows,calc}

% adds alignment keys to includegraphics
\RequirePackage[export]{adjustbox}

%%% }}}




%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Define some helper boxes
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{

% coloured boxes
\newtcbox{\inlinebox}[1][]{
    enhanced,
    box align=base,
    nobeforeafter,
    colback=DefaultBackgroundColour,
    colframe=DefaultForegroundColour,
    size=small,
    left=6pt,
    right=6pt,
    bottom=2pt,
    top=2pt,
    boxsep=2pt,
    #1
}
\newcommand{\mode}[1]{\inlinebox[#1]{\sc #1}}
\newtcbox{\timebox}[1][]{%
  on line,
  colframe=DefaultForegroundColour,
  colback=DefaultBackgroundColour,
  boxrule=0.5pt,
  arc=2pt,
  boxsep=0pt,
  left=6pt,
  right=6pt,
  top=3pt,
  bottom=2pt,
  #1
}

\newtcbox{\surveybox}[2][]{
    enhanced,
    box align=base,
    nobeforeafter,
    colframe=DefaultForegroundColour,
    colback=DefaultBackgroundColour,
    size=small,
    left=2pt,
    right=2pt,
    boxsep=2pt,
    arc=3pt,
    title={\centering #2 \hspace{0.3cm} \textbf{Survey Talk}},
    #1
}
\newcommand{\surveytalk}[2]{\surveybox{#1}{#2}}

\newtcbox{\blueskybox}[2][]{
    enhanced,
    box align=base,
    nobeforeafter,
    colframe=DefaultForegroundColour,
    colback=DefaultBackgroundColour,
    size=small,
    left=2pt,
    right=2pt,
    boxsep=2pt,
    arc=3pt,
    title={\centering #2 \hspace{0.3cm} \textbf{Blue Sky}},
    #1
}

\newtcbox{\authorpapercolorbox}[1][]{
    on line,
    colframe=DefaultForegroundColour,
    colback=DefaultBackgroundColour,
    boxrule=0.5pt,
    arc=2pt,
    boxsep=0pt,
    left=6pt,
    right=6pt,
    top=3pt,
    bottom=2pt,
    #1
}
\newcommand{\authorpaperbox}[1]{%
    \authorpapercolorbox{\parbox{3cm}{#1}} % NOTE: size picked to fit the page in it
}

\newtcbox{\sectionbox}[1][]{
    enhanced,
    box align=base,
    nobeforeafter,
    colframe=DefaultForegroundColour,
    colback=DefaultBackgroundColour,
    left=2pt,
    right=2pt,
    bottom=0pt,
    top=2pt,
    boxsep=4pt,
    %enlarge bottom initially by=4pt,
    #1
}


% Redefine the section headers
\RequirePackage{titlesec}
\titleformat*{\section}{\normalfont\Huge\bfseries\color{LinkColour}}

\newcommand{\colorsection}[1]{%
  \sectionbox[default]{\parbox{\dimexpr\linewidth-4\fboxsep}{\color{DefaultForegroundColour} #1}}
}
\titleformat{name=\subsection}[block]
  {\Large\bfseries}
  {}
  {0pt}
  {\colorsection}

%%% }}}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Define helper commands
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{

\RequirePackage{fontawesome}
\RequirePackage{xstring} %% NOTE: needed for IfStrEq

\newcommand{\pagetarget}[2]{%
  \phantomsection%
  \label{#1}%
  \hypertarget{#1}{#2}%
}


%% Command \cellcontent takes 4 arguments
%%    #1 The ID of session
%%    #2 The title of the session
%%    #3 The background color of the cell
%%    #4 The font color
\newcommand{\cellcontent}[4]{%
    \cellcolor{#4}{\color{#4}\bf \hyperlink{#1}{#2}}
}

%% Command \sessionslot takes 7 arguments:
%%    #1 the ID of the session
%%    #2 the title of the session
%%    #3 the date
%%    #4 the time slot
%%    #5 the location
%%    #6 the mode of the slot (Oral, Special, ....
%%    #7 chairs
\newcommand{\sessionslot}[7]{
	\vspace{0.5cm}
    \begin{minipage}{\linewidth} % NOTE: the use of minipage prevents the break of the page/col. between the session info.
        \pagetarget{#1}{}\subsection[\texorpdfstring{{\color{black}[#4]} #1 - #2}{#1 - #2}]{
            \begin{center}
                #1 \\
                \vspace{0.2cm}
                #2
            \end{center}
        }
        \vspace{-0.4cm}
        \begin{center}
            {\large \mode{#6} \hspace{1mm} \faMapMarker\ \textbf{#5}}
            \vspace{1mm}

            {\large \faCalendar\  #3 \hspace{1mm} \faClockO~{#4}}
            \ifx&#7&%
            \else
            	\\
            	{\large \textbf{\underline{Session chairs :}}}
            	{\large \textbf{#7}}
            \fi
        \end{center}
    \end{minipage}
    \vspace{0.4cm}
    % \rule{\linewidth}{1.5pt}
}


%% Command \presentation takes 5 arguments:
%%    #1 The type of presentation
%%    #2 the ID of the presentation in the session
%%    #3 the title
%%    #4 the authors / presenters
%%    #5 the timeslot
%%    #6 the abstract
\newcommand{\presentation}[6]{%
    \begin{spacing}{1.3}
        \noindent\pagetarget{#2}{\timebox[#1]{\textbf{#2} \resizebox{!}{3mm}{\faClockO} #5 }\ {\large\textbf{#3} } }
    \end{spacing}
    \noindent{\normalfont\textit{#4}}
    %
    \bigskip
    %
    \if@abstract
        %
        \par\noindent #6
        %
        \bigskip
    \fi
}

%% Command \survey takes 4 arguments:
%%    #1 the ID of the presentation in the session
%%    #2 the title
%%    #3 the presenter
%%    #4 the time slot allocated to the presentation
\newcommand{\survey}[4]{
%    \surveytalk{\textbf{#1} \hspace{1mm} \resizebox{!}{3mm}{\faClockO} #4}{
    \surveytalk{\resizebox{!}{3mm}{\faClockO} #4}{
        \begin{minipage}{0.97\linewidth}
            \noindent\pagetarget{#1}{\large\textbf{#2}}
            \vspace{1mm}

            \noindent{\textit{#3}}
        \end{minipage}
    }
    \bigskip
}

%% Command \bluesky takes 4 arguments:
%%    #1 the ID of the presentation in the session
%%    #2 the title
%%    #3 the presenter
%%    #4 the time slot allocated to the presentation
%%    #5 the abstract
\newcommand{\bluesky}[5]{
%    \blueskybox{\textbf{#1} \hspace{1mm} \resizebox{!}{3mm}{\faClockO} #4}{
    \blueskybox{\textbf{#1} \resizebox{!}{3mm}{\faClockO} #4}{
        \begin{minipage}{0.97\linewidth}
            \noindent\pagetarget{#1}{\large\textbf{#2}}
            \vspace{1mm}

            \noindent{\textit{#3}}

            \if@abstract
                %
                \bigskip
                %
                \par\noindent #5
            \fi
        \end{minipage}
    }
    \bigskip
}

%% Command \day takes 2 arguments
%%    #1 the day formatted in the way the user of the class want
%%    #2 the latex file containing the schedule of the day
\newcommand{\dayschedule}[2]{
    \section*{#1}
    \setcounter{tocdepth}{2}
    \etocsetlocaltop.toc{section}
    \localtableofcontents
    \newpage
    \begin{multicols*}{2}
        \noindent\input{#2}
    \end{multicols*}
}

%%% }}}


\setlength{\parindent}{0pt}
\setlength{\parskip}{1pt}

% column width in the graphical tabular depictions
% FIXME: hardcoded in the class, it could be nice to have this automatically computed
\def\tablecolwidth{2cm}
\def\tutorialtablecolwidth{5.0cm}
\def\tabletimecolwidth{2.5cm}

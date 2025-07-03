%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
% File:     INTERSPEECH2025_proceedings.cls % class file for INTERSPEECH2025 proceedings, usingthe paper kit as a starting point
%
% Usage:    \documentclass{INTERSPEECH2025_proceedings}
%
% Purpose:
%
% Style file for INTERSPEECH 2025 Conference.
% Modified from previous INTERSPEECH conferences
% Features:
%    - correct page size (175mm x 226mm)
%    - use Times-Roman font as default font (roman font) in order to achieve
%      best quality on paper and screen
%    - two-column format
%    - boldfaced, numbered, and centered section headings
%    - correct subsection and subsubsection headings
%    - \sloppy is now the default but can be changed to \fussy by
%      specifying it as a package option (i.e. \usepackage[fussy]{INTERSPEECH})
%    - use \title{xx} for title, will be typeset all uppercase
%    - use \name{xx} for author name(s) only, will be typeset in italics
%    - use \address{xx} for authors' affiliations, one per line
%    - use \email{xx} for authors' email addresses, will be typeset
%      in proportional typeface
%    - note: no need for \author nor \date
%    - optional: can use \thanks{xx} within \name, asterisk is
%      not printed after name nor in footnote
%    - optional: can use \sthanks{xx} after each name within \name,
%      footnote symbol will appear for each name and footnote
%
%
% PLEASE REPORT ANY BUGS to Simon.King@ed.ac.uk
%
% Author:  Stephen Martucci  -- martucci@cdg.nj.nec.com
% Modifications: Jyri Huopaniemi -- jyri.huopaniemi@nokia.com
%                Matti Karjalainen -- matti.karjalainen@hut.fi
%                Panayiotis Georgiou -- panayiotis.georgiou@gmail.com
%                Mattias Heldner -- heldner@ling.su.se
%                Marcin W??odarczak -- wlodarczak@ling.su.se
%                Prasanta Ghosh -- prasantag@gmail.com
%                Simon King -- Simon.King@ed.ac.uk
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


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
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

\LoadClass{article}

%%% }}}

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Colours and theme
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{

%% Colours
\RequirePackage{hyperref}
\RequirePackage[table]{xcolor}

\definecolor{Program}{HTML}{25408F}
\definecolor{ProgramAlternate}{HTML}{00AEEF}
\definecolor{LinkColour}{HTML}{25408F}

\colorlet{FooterBackgroundColour}{Program}
\colorlet{FooterForegroundColour}{white}
\colorlet{DefaultCellColour}{white}
\colorlet{DefaultColour}{black}
\colorlet{BreakCellColour}{ProgramAlternate!25!white}
\colorlet{BreakColour}{black}
\colorlet{RoomCellColour}{ProgramAlternate!15!white}
\colorlet{RoomColour}{black}
\colorlet{DebateCellColour}{LinkColour}
\colorlet{DebateColour}{white}
\colorlet{KeynoteCellColour}{LinkColour}
\colorlet{KeynoteColour}{white}
\colorlet{OralCellColour}{white}
\colorlet{OralColour}{black}
\colorlet{PosterCellColour}{ProgramAlternate}
\colorlet{PosterColour}{black}
\colorlet{SpecialCellColour}{ProgramAlternate}
\colorlet{SpecialColour}{black}
\colorlet{CeremonyColour}{black}

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
%%% Colours and theme
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% {{{
%% Header, footers and overall page format
\RequirePackage{lastpage}
\RequirePackage{fancyhdr}
\renewcommand{\headrulewidth}{0pt}

\fancypagestyle{fancy}{%
  \fancyhf{} % clear all header and footer fields
  \fancyhead[LE]{
      \begin{tikzpicture}[overlay, remember picture]%
          % \node[anchor=north, inner sep=0,outer sep=0] at (current page.north){\includegraphics[width=\paperwidth]{theme/standard_header_left.pdf}};
      \end{tikzpicture}
  }
  \fancyhead[LO]{
      \begin{tikzpicture}[overlay, remember picture]%
          % \node[anchor=north, inner sep=0,outer sep=0] at (current page.north) {\includegraphics[width=\paperwidth]{theme/standard_header_right.pdf}};
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
\RequirePackage[most]{tcolorbox}
\newtcbox{\inlinebox}[1][]{
    enhanced,
    box align=base,
    nobeforeafter,
    colback=ProgramAlternate!25!white,
    colframe=Program,
    size=small,
    left=6pt,
    right=6pt,
    bottom=2pt,
    top=2pt,
    boxsep=2pt,
    #1
}
\newcommand{\mode}[1]{\inlinebox{\sc #1}}
\newtcbox{\timebox}[1][]{
    on line,
    colframe=Program,
    colback=ProgramAlternate!25!white,
    boxrule=0.5pt,
    arc=2pt,
    boxsep=0pt,
    left=6pt,
    right=6pt,
    top=3pt,
    bottom=2pt,
    #1
}
\newtcbox{\authorpapercolorbox}[1][]{
    on line,
    colframe=Program,
    colback=ProgramAlternate!25!white,
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
    \authorpapercolorbox{\parbox{2.3cm}{#1}} % NOTE: size picked to fit the page in it
}
\newtcbox{\sectionbox}[1][]{
    enhanced,
    box align=base,
    nobeforeafter,
    colback=LinkColour,
    colframe=LinkColour,
    left=0pt,
    right=0pt,
    bottom=0pt,
    top=0pt,
    boxsep=4pt,
    %enlarge bottom initially by=4pt,
    #1
}


% Redefine the section headers
\RequirePackage{titlesec}
\titleformat*{\section}{\normalfont\Huge\bfseries\color{LinkColour}}

\newcommand{\colorsection}[1]{%
  \sectionbox{\parbox{\dimexpr\linewidth-4\fboxsep}{\color{white} #1}}
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


%% Command \paper takes 5 arguments:
%%    #1 the ID of the presentation in the session
%%    #2 the title
%%    #3 the authors
%%    #4 the presenters
%%    #5 the abstract
\newcommand{\paper}[5]{%
    \begin{spacing}{1.3}
        \noindent\pagetarget{#1}{\timebox{ \textbf{#1} }\ {\large\textbf{#2} } }
    \end{spacing}
    \noindent{\normalfont\textit{#3}}
    %
    \bigskip
    %
    \par\noindent{\textbf{Presenter(s):} \normalfont\textit{#4}}
    \bigskip
    %
    \if@abstract
        %
        \par\noindent \textbf{Abstract:}
        \par #5
        %
        \bigskip
    \fi
}
%%% }}}

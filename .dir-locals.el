;; Directory Local Variables            -*- no-byte-compile: t -*-
;; For more information see (info "(emacs) Directory Variables")

(
 (python-ts-mode . ((dape-command . (debugpy
                                     :program (executable-find"is_pub")
                                     :args [
                                            "-l" "log_app.json" "generate_app_data" "../data/ForPublicationCommittee/config.yaml" "output/app_data"
                                            ]))))
 )

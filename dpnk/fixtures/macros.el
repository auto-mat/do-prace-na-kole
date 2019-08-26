(defun to-mommy (value-name)
  "transform the json to a mommy make call"
  (interactive "sEnter value name:\n")
  (require 'json)
  (let (
        (json-txt (buffer-substring (mark) (point)))
        )
    (let (
          (json-lst (json-read-from-string json-txt))
          )
      (kill-region (mark) (point))
      (insert
       (format "self.%s = mommy.make(  # was pk=%s\n        \"%s\",\n"
               value-name
               (cdr (assoc 'pk json-lst))
               (cdr (assoc 'model json-lst))
               ))
      (dolist (v (cdr (assoc 'fields json-lst)))
        (let ((val-str (cond
                        ((stringp (cdr v)) (format "\"%s\"" (cdr v)))
                        ((booleanp (cdr v)) (if (cdr v) "True" "None"))
                        ((eq (cdr v) json-null) "None")
                        ((eq (cdr v) json-false) "False")
                        (t (format "%s" (cdr v))))
                       ))
          (insert (format "        %s = %s,\n" (car v) val-str)))
        )))
  (insert "    )")
  )

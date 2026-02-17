
### Entry

One log entry begin with a type keyword like "LOG", ends before next type keyword.

Single-line entry:
```
LOG  : General      f:0, t:1771295104050> ERROR: mods isn't a valid workshop item ID
```

Multi-line entry:
```
ERROR: General      f:0, t:1771295219628> ExceptionLogger.logException> Exception thrown
	java.lang.Exception: Fluid not found: Alcohol. line: fluid 0.1 [Alcohol] at InputScript.OnPostWorldDictionaryInit(InputScript.java:965).
	Stack trace:
		zombie.scripting.entity.components.crafting.InputScript.OnPostWorldDictionaryInit(InputScript.java:965)
		zombie.scripting.entity.components.crafting.InputScript.OnPostWorldDictionaryInit(InputScript.java:874)
		zombie.scripting.entity.components.crafting.CraftRecipe.OnPostWorldDictionaryInit(CraftRecipe.java:805)
		zombie.scripting.ScriptBucketCollection.OnPostWorldDictionaryInit(ScriptBucketCollection.java:188)
		zombie.scripting.ScriptManager.PostWorldDictionaryInit(ScriptManager.java:1669)
		zombie.iso.IsoWorld.init(IsoWorld.java:2248)
		zombie.gameStates.GameLoadingState$1.runInner(GameLoadingState.java:334)
		zombie.gameStates.GameLoadingState$1.run(GameLoadingState.java:294)
		java.base/java.lang.Thread.run(Unknown Source)
```

Keywords: LOG, WARN, ERROR


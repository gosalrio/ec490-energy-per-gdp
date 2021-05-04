library(tidyverse)
library(sjPlot)
library(readxl)

final <- read_excel("Documents/SP21/EC490/API_NY.GDP.MKTP.CD_DS2_en_csv_v2_2017804/final.xlsx")
View(final)

correlations = final %>% 
  group_by(Country) %>% 
  summarise(cor(x=TIME, y=energyPerGDP))

View(correlations)

final %>% 
  filter(energyPerGDP > 0) %>% 
  group_by(IncomeGroup) %>% 
  summarise(median(energyPerGDP),
            mean(energyPerGDP),
            range(energyPerGDP))

final %>%
  filter(IncomeGroup == "Low") %>% 
  ggplot(aes(x=TIME, y=energyPerGDP)) +
  geom_point() +
  geom_smooth(method="lm") +
  facet_wrap(~Country)

final %>% 
  filter(Country == 'Indonesia') %>% 
  ggplot(aes(x=TIME)) +
  geom_point(aes(y=Energy), color='red') +
  geom_point(aes(y = GDP), color='blue')

final %>% 
  filter(Year > 1990 & IncomeGroup == "High" & Country != "United States" ) %>% 
  ggplot(aes(x=Energy, y=GDP)) +
  geom_point() +
  geom_smooth(method="lm")

final %>% 
  filter(IncomeGroup == "Upper middle" & energyPerGDP < 1) %>% 
  ggplot(aes(x=Year,y=energyPerGDP)) +
  geom_point() +
  geom_smooth(formula = y ~ x^2, method = 'loess') +
  facet_wrap(~Country)

final %>% 
  filter(Country == "Malaysia") %>% 
  ggplot(aes(x=Year,y=energyPerGDP)) +
  geom_point() +
  geom_smooth(formula = y ~ x^2, method = 'loess')

#urban / rural, size of urban?
#energyCost / Watt
#kWh/$
# manufacturing value, industrialization level, 
#renewablesModel = final %>% 
#  filter(energyPerGDP > 0 & IncomeGroup != "Low") %>% 
#  lm(formula = Renewables ~ Size, data = .)

#summary(renewablesModel)

model1 = final %>% 
  filter(energyPerGDP > 0 & IncomeGroup != "Low") %>% 
  lm(formula = log(energyPerGDP) ~ Year + Developed, data = .)
summary(model1)

model1 %>%
  plot_model(type="pred", terms = c("Year", "Developed"))


renewablesModel = final %>% 
  filter(energyPerGDP > 0 & IncomeGroup != "Low" & Renewables > 0) %>% 
  lm(formula = log(energyPerGDP) ~ Renewables, data = .)

renewablesModel %>% 
  plot_model(type="pred")

model_better = final %>% 
  filter(energyPerGDP > 0  & IncomeGroup != "Low" & Internet > 0 & Renewables > 0) %>% 
  lm(formula = log(energyPerGDP) ~ Year + Size +
       Developed + log(Employment) + Years_of_Schooling +
       log(Renewables) + log(Internet), data = .)

summary(model_better)
  
model_all = final %>% 
  filter(energyPerGDP > 0 & IncomeGroup != "Low") %>% 
  lm(formula = log(energyPerGDP) ~ Year + Size +
       Developed + log(Employment) + Years_of_Schooling +
       Renewables + log(Internet), data = .)

summary(model_all)

model_all %>% 
  plot_model(type="pred", terms = c("Year", "Developed"))
  
figure;
hold on;
plot(spectr_target.freq, (spectr_target.powspctrm), 'linewidth', 2)
plot(spectr_standard.freq, (spectr_standard.powspctrm), 'linewidth', 2)
plot(spectr_novelty.freq, (spectr_novelty.powspctrm), 'linewidth', 2)
legend('target', 'standard', 'novelty')
xlabel('Frequency (Hz)')
ylabel('Power (\mu V^2)')